# Cloud Deployment Guidance Conversation Summary

## Question

What is needed to pull and run the website on a cloud server, and whether a domain name and HTTPS are required.

## Guidance

- The repository supports production-style deployment with Docker Compose, an Nginx reverse proxy, a FastAPI API, and a Next.js web service.
- A domain is not required for an initial IP-based HTTP smoke test.
- A domain and HTTPS are strongly recommended for any public deployment because the site handles user identifiers, can use remote agents, and may serve remote media.
- A domain also enables standard Let's Encrypt certificate issuance and avoids browser mixed-content restrictions.

## Main Operational Steps

1. Provision a Linux server with Docker Engine, Docker Compose plugin, Git, and firewall access for ports 80 and 443.
2. Clone the repository, copy `.env.example` to `.env`, and set production secrets and agent configuration.
3. Build and start with `docker compose up --build -d`; verify `/health` through the Nginx port.
4. Point the DNS A record to the server, then terminate HTTPS at a host Nginx or cloud load balancer with an ACME certificate.
5. Keep the application's existing SSE proxy settings and persist the named Docker volume that contains SQLite data.
