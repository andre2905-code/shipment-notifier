import { ApartmentType } from "../types";

const BASE_URL = "http://localhost:8000";

export async function fetchApartments() {
  const response = await fetch(`${BASE_URL}/listar-moradores`);
  if (!response.ok) {
    throw new Error("Failed to fetch apartments");
  }
  return response.json();
}

export async function fetchNotifications() {
  const response = await fetch(`${BASE_URL}/encomendas-pendentes`);
  if (!response.ok) {
    throw new Error("Failed to fetch notifications");
  }
  return response.json();
}

export async function createApartment(data: ApartmentType) {
  const response = await fetch(`${BASE_URL}/cadastrar-morador`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error("Failed to create apartment");
  }
  return response.json();
}

export async function updateNotificationStatus(codigo: string) {
  const response = await fetch(`${BASE_URL}/registrar-retirada`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ codigo_retirada: codigo }),
  });
  if (!response.ok) {
    throw new Error("Failed to update notification status");
  }
  return response.json();
}

export async function createNotification(data: any) {
  const response = await fetch(`${BASE_URL}/registrar-encomenda`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error("Failed to create notification");
  }
  return response.json();
}