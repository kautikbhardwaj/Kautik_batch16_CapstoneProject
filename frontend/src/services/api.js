import axios from 'axios';

const API_BASE = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchOverview = (provider = 'ALL', environment = 'ALL', days = 30) =>
  apiClient.get(`/dashboard/overview?provider=${provider}&environment=${environment}&days=${days}`);

export const fetchCostRecords = (params) =>
  apiClient.get('/costs/records', { params });

export const fetchResources = (params) =>
  apiClient.get('/resources', { params });

export const fetchAlertRules = () =>
  apiClient.get('/alerts/rules');

export const createAlertRule = (ruleData) =>
  apiClient.post('/alerts/rules', ruleData);

export const deleteAlertRule = (ruleId) =>
  apiClient.delete(`/alerts/rules/${ruleId}`);

export const fetchAlertIncidents = (status) =>
  apiClient.get('/alerts/incidents', { params: { status } });

export const resolveAlertIncident = (incidentId) =>
  apiClient.post(`/alerts/incidents/${incidentId}/resolve`);

export const fetchRecommendations = (status = 'pending') =>
  apiClient.get('/recommendations', { params: { status } });

export const updateRecommendationStatus = (recId, status) =>
  apiClient.post(`/recommendations/${recId}/status?status=${status}`);

export const triggerCloudSync = (days = 30) =>
  apiClient.post(`/sync/trigger?days=${days}`);
