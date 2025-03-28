// src/services/PrinterService.ts
import axiosInstance from '../lib/axios';

export interface Printer {
  id?: number;
  name: string;
  brand: string;
  model: string;
  ip_address: string;
  status?: string;
  client_id?: number;
  agent_id?: number;
  last_check?: string;
  serial_number?: string;
  printer_data?: any;
}

export interface PrinterSupplies {
  toners: {
    black: number;
    cyan: number;
    magenta: number;
    yellow: number;
  };
  drums: {
    black: number;
    cyan: number;
    magenta: number;
    yellow: number;
  };
}

export interface PrinterCounters {
  total: number;
  color: number;
  black_and_white: number;
  copies: number;
  prints: number;
  scans: number;
}

export interface PrinterReport {
  total_printers: number;
  printers_by_status: Record<string, number>;
  printers_by_brand: Record<string, number>;
  critical_supplies: Array<{
    printer_id: number;
    printer_name: string;
    critical_supplies: any[];
  }>;
}

export class PrinterService {
  static async getPrinters(agentId?: number): Promise<Printer[]> {
    try {
      // MODIFICADO: Usar URL absoluta HTTPS para esta solicitud que causa problemas
      const params = agentId ? { agent_id: agentId } : {};
      
      // Usar URL absoluta con HTTPS para evitar problemas de contenido mixto
      const response = await axiosInstance.get('https://copierconnectremote.com/api/v1/monitor/printers', { params });
      
      return response.data || [];
    } catch (error) {
      console.error("Error fetching printers:", error);
      throw error;
    }
  }

  // El resto de los métodos permanecen igual...

  static async getPrinterById(printerId: number): Promise<Printer | null> {
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching printer ${printerId}:`, error);
      return null;
    }
  }

  static async createPrinter(printerData: Printer): Promise<Printer> {
    try {
      const response = await axiosInstance.post('/monitor/printers/create', printerData);
      return response.data;
    } catch (error) {
      console.error("Error creating printer:", error);
      throw error;
    }
  }

  static async updatePrinter(printerId: number, printerData: Partial<Printer>): Promise<Printer> {
    try {
      const response = await axiosInstance.post('/monitor/printers/update', {
        ...printerData,
        printer_id: printerId,
        agent_id: printerData.agent_id || 1
      });
      return response.data;
    } catch (error) {
      console.error(`Error updating printer ${printerId}:`, error);
      throw error;
    }
  }

  static async deletePrinter(printerId: number): Promise<boolean> {
    try {
      await axiosInstance.delete(`/monitor/printers/${printerId}`);
      return true;
    } catch (error) {
      console.error(`Error deleting printer ${printerId}:`, error);
      return false;
    }
  }

  static async getPrinterSupplies(printerId: number): Promise<PrinterSupplies | null> {
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}/supplies`);
      return response.data.supplies;
    } catch (error) {
      console.error(`Error fetching supplies for printer ${printerId}:`, error);
      return null;
    }
  }

  static async getPrinterCounters(printerId: number): Promise<PrinterCounters | null> {
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}/counters`);
      return response.data.counters;
    } catch (error) {
      console.error(`Error fetching counters for printer ${printerId}:`, error);
      return null;
    }
  }

  static async getPrinterHistory(printerId: number, days: number = 7): Promise<any> {
    try {
      const response = await axiosInstance.get(`/monitor/printers/${printerId}/history`, {
        params: { days }
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching history for printer ${printerId}:`, error);
      return null;
    }
  }

  static async getPrinterReport(): Promise<PrinterReport | null> {
    try {
      const response = await axiosInstance.get('/monitor/printers/report');
      return response.data;
    } catch (error) {
      console.error("Error fetching printer report:", error);
      return null;
    }
  }

  static async getCriticalSupplies(): Promise<any[]> {
    try {
      const response = await axiosInstance.get('/monitor/printers/critical-supplies');
      return response.data || [];
    } catch (error) {
      console.error("Error fetching critical supplies:", error);
      return [];
    }
  }

  static async updatePrinterData(printerId: number, printerData: any, agentId?: number): Promise<Printer> {
    try {
      const response = await axiosInstance.post('/monitor/printers/update', {
        printer_data: printerData,
        agent_id: agentId || 1
      });
      return response.data;
    } catch (error) {
      console.error(`Error updating printer data for ${printerId}:`, error);
      throw error;
    }
  }
  
  static async countByStatus(): Promise<Record<string, number>> {
    try {
      const printers = await this.getPrinters();
      
      const result = {
        total: printers.length,
        online: 0,
        offline: 0,
        error: 0
      };
      
      printers.forEach(printer => {
        if (printer.status === 'online') result.online++;
        else if (printer.status === 'offline') result.offline++;
        else if (printer.status === 'error') result.error++;
      });
      
      return result;
    } catch (error) {
      console.error("Error counting printers by status:", error);
      return {
        total: 0,
        online: 0,
        offline: 0,
        error: 0
      };
    }
  }
  
  static async getPrintersByClient(clientId: number): Promise<Printer[]> {
    try {
      const printers = await this.getPrinters();
      return printers.filter(printer => printer.client_id === clientId);
    } catch (error) {
      console.error(`Error fetching printers for client ${clientId}:`, error);
      return [];
    }
  }
}