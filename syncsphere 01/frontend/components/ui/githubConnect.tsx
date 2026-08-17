import React from "react";
import { API_BASE_URL, integrationApi } from "../../shared/services/api-client";

export default function GithubConnectButton() {

  const connectGithub = () => {
    integrationApi.connectGithub();
  };

  const connectSlack = () => {
    integrationApi.connectSlack();
  }

  const connectGoogle = () => {
    integrationApi.connectGoogle();
  }
  return (
    <div style={{ display: "flex", gap: "12px" }}>
      <button
        onClick={connectGithub}
        style={{
          padding: "12px 24px",
          borderRadius: "8px",
          background: "#24292f",
          color: "white",
          border: "none",
          cursor: "pointer",
          fontSize: "16px"
        }}
      >
        Connect GitHub
      </button>

      <button
        onClick={connectSlack}
        style={{
          padding: "12px 24px",
          borderRadius: "8px",
          background: "#4A154B", // Slack purple
          color: "white",
          border: "none",
          cursor: "pointer",
          fontSize: "16px"
        }}
      >
        Connect Slack
      </button>

      <button
        onClick={connectGoogle}
        style={{
          padding: "12px 24px",
          borderRadius: "8px",
          background: "#4A154B", // Slack purple
          color: "white",
          border: "none",
          cursor: "pointer",
          fontSize: "16px"
        }}
      >
        Connect Google
      </button>
    </div>
  )
}