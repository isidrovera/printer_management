// src/services/PrinterServiceInstall.ts
import axiosInstance from '../lib/axios';

// Tipos
export interface Printer {
  id: number;
  ip_address: string;
  brand: string;
  model: string;
  status: string;
  agent_id: number;
  is_active: boolean;
  name?: string;
  printer_data?: any;
}

export interface PrinterCounters {
  printer_id: number;
  name?: string;
  counters: {
    total: number;
    color: number;
    black_and_white: number;
    copies: number;
    prints: number;
    scans: number;
  };
}

export interface PrinterSupplies {
  printer_id: number;
  name?: string;
  supplies: {
    toners: {
      black: { level: number; status: string };
      cyan: { level: number; status: string };
      magenta: { level: number; status: string };
      yellow: { level: number; status: string };
    };
    drums: {
      black: { level: number; status: string };
      cyan: { level: number; status: string };
      magenta: { level: number; status: string };
      yellow: { level: number; status: string };
    };
  };
}

export interface InstallPrinterRequest {
  printer_ip: string;
  driver_id: number;
}

export interface InstallPrinterResponse {
  status: string;
  message: string;
  details: {
    printer_ip: string;
    driver: string;
  };
}

// Servicio
export const PrinterService = {
  // Obtener todas las impresoras para monitoreo
  async getMonitoredPrinters(): Promise<Printer[]> {
    try {
      const response = await axiosInstance.get(`/printers/monitor`);
      return response.data;
    } catch (error) {
      console.error('Error fetching monitored printers', error);
      throw error;
    }
  },

  // Obtener impresoras por agente
  async getAgentPrinters(agentId: number): Promise<Printer[]> {
    try {
      const response = await axiosInstance.get(`/printers/monitored/${agentId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching printers for agent ${agentId}`, error);
      throw error;
    }
  },

  // Obtener contadores de una impresora
  async getPrinterCounters(printerId: number): Promise<PrinterCounters> {
    try {
      const response = await axiosInstance.get(`/printers/${printerId}/counters`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching counters for printer ${printerId}`, error);
      throw error;
    }
  },

  // Obtener suministros de una impresora
  async getPrinterSupplies(printerId: number): Promise<PrinterSupplies> {
    try {
      const response = await axiosInstance.get(`/printers/${printerId}/supplies`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching supplies for printer ${printerId}`, error);
      throw error;
    }
  },

  // Instalar una impresora en un agente
  async installPrinter(
    agentToken: string,
    installData: InstallPrinterRequest
  ): Promise<InstallPrinterResponse> {
    try {
      const response = await axiosInstance.post(
        `/printers/install/${agentToken}`,
        installData
      );
      return response.data;
    } catch (error) {
      console.error('Error installing printer', error);
      throw error;
    }
  }
};

export default PrinterService;