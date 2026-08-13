export function formatConnectorError(err: any, provider: string): string {
    const errorString = (typeof err === 'object' ? JSON.stringify(err) : String(err)).toLowerCase();

    if (errorString.includes('expired') || errorString.includes('authorization_required') || errorString.includes('missing_oauth')) {
        return `${provider} authorization has expired. Reconnect ${provider} to continue.`;
    }

    if (errorString.includes('permission') || errorString.includes('scope') || errorString.includes('forbidden') || errorString.includes('not in channel')) {
        return `${provider} authorization is missing required permissions.`;
    }

    if (errorString.includes('inactive') || errorString.includes('account_inactive')) {
        return `${provider} account is inactive. Reconnect or select an active ${provider} account.`;
    }

    if (errorString.includes('rate limit') || errorString.includes('429') || errorString.includes('too many requests')) {
        return `Service rate limit reached. Please try again shortly.`;
    }

    if (errorString.includes('network error') || errorString.includes('econnrefused') || errorString.includes('timeout')) {
        return `Unable to reach the service. Please try again.`;
    }

    // User requirement: Do not hide the original exception. Show actual safe Google error reason.
    try {
        if (typeof err === 'object' && err !== null) {
            return err.message || err.error || JSON.stringify(err);
        }
    } catch { }

    return String(err);
}
