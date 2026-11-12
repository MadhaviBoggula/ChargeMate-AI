
/* =========================
   USER TYPES
========================= */

export type UserRole = "customer" | "staff" | "admin";

export interface User {
  id: number | string;
  name: string;
  email: string;
  mobile: string;
  role: UserRole;
  dateOfBirth?: string;
  vehicleId?: number | string;
  addressId?: number | string;
  createdAt?: string;
  updatedAt?: string;
}

/* =========================
   VEHICLE TYPES
========================= */

export type VehicleType = "two-wheeler" | "three-wheeler" | "four-wheeler";

export interface Vehicle {
  id: number | string;
  type: VehicleType;
  model: string;
  vehicleNumber: string;
  batteryCapacity?: number;
  batteryVoltage?: number;
  chargingTime?: number;
  connectorTypes?: string[];
}

/* =========================
   CHARGING STATION TYPES
========================= */

export type ChargerType = "AC" | "DC";

export type AvailabilityStatus = "available" | "occupied" | "unavailable";

export interface ChargingStation {
  id: number | string;
  name: string;
  description?: string;
  address: string;
  city: string;
  state: string;
  pincode?: string;
  latitude?: number;
  longitude?: number;
  chargerType?: ChargerType;
  connectorTypes: string[];
  chargingPower: number;
  pricePerUnit: number;
  availabilityStatus: AvailabilityStatus;
  isActive: boolean;
  compatibleVehicleTypes?: VehicleType[];
}

/* =========================
   API RESPONSE TYPES
========================= */

export interface ApiResponse<T> {
  message?: string;
  data: T;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}
