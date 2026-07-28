import re
import logging
from typing import Dict, Any, Optional, List
from syncsphere.shared_kernel.types.result import Result
from syncsphere.ai.domain.entities.prompt import PromptTemplate, PromptVersion
from syncsphere.ai.domain.repositories import PromptTemplateRepository, PromptVersionRepository
from syncsphere.ai.domain.exceptions import PromptCompilationException

logger = logging.getLogger("syncsphere.ai.application.services.prompt_engine")

class PromptEngine:
    """
    PromptEngine manages prompt compilation, template inheritance,
    variable substitutions (including nesting), and structural validation.
    """
    def __init__(
        self,
        template_repo: PromptTemplateRepository,
        version_repo: PromptVersionRepository
    ) -> None:
        self.template_repo = template_repo
        self.version_repo = version_repo

    def validate_variables(self, template: PromptTemplate, context: Dict[str, Any]) -> List[str]:
        """Checks if all required variables are present in the rendering context."""
        missing = []
        for var in template.variables:
            if var.required and var.name not in context and var.default_val is None:
                missing.append(var.name)
        return missing

    def render_string(self, template_str: str, context: Dict[str, Any], max_depth: int = 5) -> str:
        """
        Recursively replaces placeholders in a template string using context dictionary values.
        Supports nested variable substitution (e.g., variable containing other placeholders).
        """
        pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}")
        
        current_str = template_str
        for depth in range(max_depth):
            matches = pattern.findall(current_str)
            if not matches:
                break
                
            has_substitutions = False
            for var_name in matches:
                # Find variable in context
                val = context.get(var_name)
                
                # If not in context, check for defaults (handled at engine validation level)
                if val is None:
                    # Keep raw placeholder if undefined in context
                    continue
                    
                placeholder = "{{" + var_name + "}}"
                # Handle standard spacing variants
                current_str = re.sub(
                    r"\{\{\s*" + re.escape(var_name) + r"\s*\}\}",
                    str(val),
                    current_str
                )
                has_substitutions = True
                
            if not has_substitutions:
                break
                
        return current_str

    async def compile(
        self,
        org_id: str,
        template_name: str,
        variables: Dict[str, Any],
        version_num: Optional[int] = None
    ) -> Result[Dict[str, str], Exception]:
        """
        Loads the template and specific version, performs template inheritance
        if a parent version is specified, validates variable bindings, and renders
        both the system and user templates.
        """
        logger.info("Compiling prompt '%s' (version: %s) for org: %s", template_name, version_num, org_id)
        
        template = await self.template_repo.get_by_name(org_id, template_name)
        if not template:
            return Result.fail(PromptCompilationException(template_name, "Prompt template not found."))

        # Validate variables before compilation
        missing_vars = self.validate_variables(template, variables)
        if missing_vars:
            return Result.fail(PromptCompilationException(
                template_name,
                f"Missing required variables: {', '.join(missing_vars)}"
            ))

        # Build full rendering context including defaults
        render_context = {}
        for var in template.variables:
            if var.default_val is not None:
                render_context[var.name] = var.default_val
        render_context.update(variables)

        # Retrieve specific version or the latest version
        target_version_num = version_num or template.latest_version
        if target_version_num <= 0:
            return Result.fail(PromptCompilationException(template_name, "No versions registered for this template."))

        version = await self.version_repo.get_by_version(template.id, target_version_num)
        if not version:
            return Result.fail(PromptCompilationException(
                template_name,
                f"Prompt version {target_version_num} not found."
            ))

        # Compile templates
        system_template = version.system_template
        user_template = version.user_template

        # Handle Template Inheritance if parent_version_id is set
        if version.parent_version_id:
            # Recursively load parent templates
            parent = await self.version_repo.get_by_version(template.id, target_version_num - 1)
            if parent:
                # Merge templates: parent system template prepended to child system template
                system_template = parent.system_template + "\n" + system_template
                user_template = parent.user_template + "\n" + user_template

        # Render templates using context
        try:
            rendered_system = self.render_string(system_template, render_context)
            rendered_user = self.render_string(user_template, render_context)
            
            return Result.ok({
                "system": rendered_system,
                "user": rendered_user,
                "hash": version.hash,
                "version": str(version.version)
            })
        except Exception as e:
            return Result.fail(PromptCompilationException(template_name, f"Render error: {str(e)}"))
