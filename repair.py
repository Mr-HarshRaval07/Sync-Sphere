import re
import sys

file_path = 'backend/src/syncsphere/approval/application/services/approval_service.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for the corrupted double-if check
pattern = re.compile(
    r'if self\.event_bus:\n\s+if self\.event_bus:\n\s+await self\.event_bus\.publish\(event\)\n\s+else:\n\s+logger\.warning\(f\'Event bus unavailable\. Dropping event: \{event\}\'\)\n\s+else:\n\s+logger\.warning\(f"Event bus unavailable\. Dropping event: \{event\}"\)',
    re.MULTILINE
)

# And another one that has "" in the first
pattern2 = re.compile(
    r'if self\.event_bus:\n\s+if self\.event_bus:\n\s+await self\.event_bus\.publish\(event\)\n\s+else:\n\s+logger\.warning\(f"Event bus unavailable\. Dropping event: \{event\}"\)\n\s+else:\n\s+logger\.warning\(f"Event bus unavailable\. Dropping event: \{event\}"\)',
    re.MULTILINE
)

# And another one that might be present
pattern3 = re.compile(
    r'if self\.event_bus:\n\s+if self\.event_bus:\n\s+await self\.event_bus\.publish\(event\)\n\s+else:\n\s+.*?\n\s+else:\n\s+.*?\n',
    re.MULTILINE
)


def replacement(m):
    return """if self.event_bus:
                    await self.event_bus.publish(event)
                else:
                    import logging; logging.warning(f"Event bus unavailable. Dropping event: {event}")
"""

content = pattern.sub(replacement, content)
content = pattern2.sub(replacement, content)
content = pattern3.sub(replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Test compilation
try:
    compile(content, file_path, 'exec')
    print("SUCCESS: Code compiles.")
except SyntaxError as e:
    print(f"FAILED: {e}")
    sys.exit(1)
