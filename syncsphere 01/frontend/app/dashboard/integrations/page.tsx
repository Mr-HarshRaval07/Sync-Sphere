"use client";
import { integrationApi } from '../../../shared/services/api-client';

export default function IntegrationsPage() {

  const connectGithub = () => {
    integrationApi.connectGithub();
  };

  const connectSlack = () => {
    integrationApi.connectSlack();
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Integrations</h1>

      <button onClick={connectGithub}>
        Connect GitHub
      </button>

      <br /><br />

      <button onClick={connectSlack}>
        Connect Slack
      </button>
    </div>
  );
}