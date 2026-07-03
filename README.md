# SentinelOps: Self-Healing Infrastructure Prototype

## System Architecture Blueprint

SentinelOps uses isolated domain containers that communicate exclusively over an explicit internal virtual network bridge interface managed by Docker.

```text
[ Client Requests ]
       │
       ├──► :8001 ──► [ auth-service ] (Generates Secure Identity Signatures)
       │
       ├──► :8002 ──► [ orders-service ] ──(Verifies Token)──► [ auth-service ]
       │
       └──► :8003 ──► [ payments-service ] (Injects 10% Intermittent Flakiness)