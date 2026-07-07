# Preferred Connections Registry
# ──────────────────────────────────────────────────────────────────
# Tells Plan Mode (/plan) which connections already exist in AtomSphere
# and should be REUSED rather than recreated.
#
# FORMAT:
#   ## [Connection Component Name in AtomSphere]
#   type: [Connector Type]
#   system: [System it connects to]
#   protocol: [REST / SOAP / JDBC / SFTP / JMS / etc.]
#   auth: [None / API Key / OAuth2 / Basic / mTLS / etc.]
#   environments: [STG, PROD / STG only / PROD only]
#   notes: [anything useful for the AI when deciding to reuse]
# ──────────────────────────────────────────────────────────────────

## CONN-POSTGRES-CLAIMS-JDBC
type: Database
system: PostgreSQL — Claims database
protocol: JDBC
auth: Username/Password (via environment extension)
environments: STG, PROD
notes: Shared DB connection for all CLAIMS domain processes. Use for any PostgreSQL query/execute in the claims schema.

## CONN-IMRIGHT-REST-V2
type: HTTP Client
system: ImageRight Document Management
protocol: REST
auth: API Key (X-API-Key header, via environment extension)
environments: STG, PROD
notes: ImageRight REST API v2. Always reuse this — never create a duplicate ImageRight connection.

## CONN-GHOSTDRAFT-REST
type: HTTP Client
system: GhostDraft Template Engine
protocol: REST
auth: OAuth2 Client Credentials (via environment extension)
environments: STG, PROD
notes: GhostDraft document generation endpoint.

## CONN-AZURE-SERVICEBUS-JMS
type: JMS
system: Azure Service Bus
protocol: AMQP (JMS wrapper)
auth: SAS Token (via environment extension)
environments: STG, PROD
notes: Event-driven processes. Reuse for any Azure Service Bus publish/subscribe.

## CONN-SFTP-MFT-GOANY
type: FTP/SFTP
system: GoAnywhere MFT
protocol: SFTP
auth: SSH Key (via environment extension)
environments: STG, PROD
notes: GoAnywhere MFT endpoint for secure file transfer.

## CONN-SALESFORCE-REST
type: Salesforce
system: Salesforce CRM
protocol: REST (Salesforce connector)
auth: OAuth2 (connected app, via environment extension)
environments: STG, PROD
notes: Reuse for all Salesforce read/write operations. Remember camelCase filter operators and required Sorts element.

# ──────────────────────────────────────────────────────────────────
# ADD YOUR OWN ENTRIES BELOW — same format as above
# ──────────────────────────────────────────────────────────────────
