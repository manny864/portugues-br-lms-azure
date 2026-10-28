/**
 * /api/progress/index.js
 * Azure Function (Managed Function integrada en Azure Static Web Apps)
 * Conecta GET /api/progress y POST /api/progress con Azure Cosmos DB (NoSQL Serverless).
 */

const { CosmosClient } = require('@azure/cosmos');

const endpoint = process.env.COSMOS_DB_ENDPOINT;
const key = process.env.COSMOS_DB_KEY;
const databaseId = process.env.COSMOS_DB_DATABASE || 'ptbrLmsDb';
const containerId = process.env.COSMOS_DB_CONTAINER || 'userProgress';

function getAuthenticatedUserId(req) {
  const header = req.headers['x-ms-client-principal'];
  if (header) {
    try {
      const encoded = Buffer.from(header, 'base64');
      const decoded = encoded.toString('ascii');
      const principal = JSON.parse(decoded);
      if (principal && principal.userId) {
        return principal.userId;
      }
    } catch (e) {
      // Fallback al userId del query/body
    }
  }
  return (req.query && req.query.userId) || (req.body && req.body.userId) || 'anonymous';
}

module.exports = async function (context, req) {
  const userId = getAuthenticatedUserId(req);

  if (!endpoint || !key) {
    context.res = {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: {
        status: 'local-fallback',
        userId,
        message: 'Variables COSMOS_DB_ENDPOINT / COSMOS_DB_KEY no configuradas aún; operando en modo híbrido.'
      }
    };
    return;
  }

  const client = new CosmosClient({ endpoint, key });
  const container = client.database(databaseId).container(containerId);

  try {
    if (req.method === 'GET') {
      const { resource } = await container.item(userId, userId).read();
      context.res = {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: resource || { userId, completedLessons: [], quizScores: {} }
      };
      return;
    }

    if (req.method === 'POST') {
      const payload = {
        ...req.body,
        id: userId,
        userId,
        updatedAt: new Date().toISOString()
      };
      const { resource } = await container.items.upsert(payload);
      context.res = {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: resource
      };
      return;
    }

    context.res = { status: 405, body: 'Method Not Allowed' };
  } catch (error) {
    context.log.error('Error en Azure Function /api/progress:', error);
    context.res = {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
      body: { error: error.message }
    };
  }
};
