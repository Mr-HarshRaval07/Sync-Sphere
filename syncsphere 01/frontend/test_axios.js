const axios = require('axios');

async function run() {
    try {
        const apiClient = axios.create({
            baseURL: 'http://127.0.0.1:8001',
            headers: {
                'Authorization': 'Bearer test',
                'Content-Type': 'application/json'
            }
        });
        
        const r = await apiClient.post('/v1/tasks/plan-with-ai', {
            prompt: "Create a high-priority task called Launch SyncSphere Website and assign it to Janhvi. Complete it by August 15, 2026. Create a GitHub issue with the task details, notify my configured Slack channel, send an email to janhvic24@gmail.com with the task title, assignee, priority, status, and due date, add the task to my connected Google Sheet, and create a Google Calendar event for August 15, 2026. Automatically recommend and select all relevant integrations. I only want to review the plan and click Apply & Execute."
        });
        
        console.log("Raw Response Data (r.data):");
        console.log(JSON.stringify(r.data, null, 2));
        
        console.log("\nParsed Data (r.data.data):");
        console.log(JSON.stringify(r.data.data, null, 2));

        console.log("\nDoes task exist in r.data.data?", !!r.data.data?.task);
    } catch (e) {
        console.error(e.response ? e.response.data : e.message);
    }
}

run();
