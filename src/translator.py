"""
PHI-INFINITY (Phi-Infinity) - Universal Bidirectional Translation Protocol
Interfaccia Operativa: Substrato Relazionale (Phi) <-> Linguaggio Discreto (H)
Author: Massimiliano Brighindi (2026)
"""
import numpy as np

class PhiBidirectionalTranslator:
    def __init__(self, beta=0.25):
        self.beta = beta

    def deconstruct_human_to_phi(self, entity_name, is_rigid_statement=False, energy_bias=1.0, resource_bias=1.0):
        """
        Direzione 2: T_H_Phi (Dal Linguaggio Umano al Substrato Relazionale)
        De-reifica sostantivi e dogmi in nodi di calcolo con stress iniziale proporzionale alla rigidità.
        """
        initial_R = 1.2 if is_rigid_statement else 0.01
        incomp = abs((energy_bias / (resource_bias + 1e-3)) - 1.0)
        initial_R += 0.5 * (incomp ** 2)
        
        return {
            "entity": entity_name,
            "mapped_to": "Cluster di Nodi C",
            "initial_Ri": float(initial_R),
            "state_vector": [float(energy_bias), float(resource_bias), 1.0],
            "hypothesis": "M_C(tau) > 1.0 da verificare per evoluzione dinamica"
        }

    def translate_phi_to_human(self, M_C, R_C, d_tau, K_ext, K_int, name="X"):
        """
        Direzione 1: T_Phi_H (Dal Substrato Relazionale al Linguaggio Umano)
        Converte grandezze topologiche in sintassi umana trasparente senza forzature probabilistiche.
        """
        # 1. Regola dell'Entificazione Condizionata
        if M_C > 1.5 and R_C < 0.1:
            stato = f"L'entita '{name}' e stabile e persistente nell'attuale configurazione relazionale (M_C = {M_C:.2f})."
        elif M_C >= 1.0:
            stato = f"L'entita '{name}' e in regime di tensione critica/transizione (M_C = {M_C:.2f}, R_C = {R_C:.3f}); mutera se il flusso esterno supera la soglia critica."
        else:
            stato = f"L'entita '{name}' ha superato la soglia critica (M_C = {M_C:.2f} <= 1.0): confine dissolto e nodi in riconfigurazione nel contesto."

        # 2. Regola dell'Apertura Esplicita e Flussi
        if K_ext < 0.1 * (K_int + 1e-5):
            apertura = "Chiusura sistemica forte (bassa interferenza esterna)."
        elif K_ext > K_int:
            apertura = f"Dominanza dei flussi ambientali (K_ext = {K_ext:.2f} > K_int = {K_int:.2f}): il fenomeno dipende strettamente dal contesto."
        else:
            apertura = f"Interfaccia attiva permeabile (K_ext = {K_ext:.2f}, K_int = {K_int:.2f})."

        # 3. Tempo proprio locale
        dinamica = f"Tasso di mutamento proprio locale d_tau = {d_tau:.4f}."
        
        return f"{stato} | {apertura} | {dinamica}"
