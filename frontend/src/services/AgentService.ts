// src/services/AgentService.ts
import axiosInstance from '../lib/axios';

export interface Agent {
  id?: number;
  token: string;
  hostname: string;
  username: string;
  ip_address: string;
  device_type: string;
  system_info: any;
  status: string;
}

export interface AgentCreate {
  client_token: string;
  hostname: string;
  username: string;
  ip_address: string;
  device_type: string;
  system_info: any;
}

export interface AgentUpdate {
  agent_token: string;
  hostname?: string;
  username?: string;
  ip_address?: string;
  device_type?: string;
  system_info?: any;
}

export class AgentService {
  static async getAgents(search?: string): Promise<Agent[]> {
    try {
      const endpoint = search && search.trim() !== '' 
        ? `/agents/search/${encodeURIComponent(search)}` 
        : '/agents/';
      
      const response = await axiosInstance.get(endpoint);
      return response.data?.agents || [];
    } catch (error) {
      console.error("Error fetching agents:", error);
      throw error;
    }
  }

  static async getAgentById(agentId: number): Promise<Agent | null> {
    try {
      const response = await axiosInstance.get(`/api/v1/agents/${agentId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching agent ${agentId}:`, error);
      return null;
    }
  }

  static async createAgent(agentData: AgentCreate): Promise<Agent> {
    try {
      const response = await axiosInstance.post('/api/v1/agents/', agentData);
      return response.data;
    } catch (error) {
      console.error("Error creating agent:", error);
      throw error;
    }
  }

  static async updateAgent(agentData: AgentUpdate): Promise<Agent> {
    try {
      const response = await axiosInstance.put('/api/v1/agents/update', agentData);
      return response.data;
    } catch (error) {
      console.error(`Error updating agent:`, error);
      throw error;
    }
  }

  static async deleteAgent(agentId: number): Promise<boolean> {
    try {
      await axiosInstance.delete(`/api/v1/agents/${agentId}`);
      return true;
    } catch (error) {
      console.error(`Error deleting agent ${agentId}:`, error);
      return false;
    }
  }

  static async registerAgent(agentData: AgentCreate): Promise<Agent> {
    try {
      const response = await axiosInstance.post('/api/v1/agents/register', agentData);
      return response.data;
    } catch (error) {
      console.error("Error registering agent:", error);
      throw error;
    }
  }
}