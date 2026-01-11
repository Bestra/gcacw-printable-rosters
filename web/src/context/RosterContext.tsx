import { createContext, useContext, type ReactNode } from "react";

interface RosterContextValue {
  gameId: string | undefined;
  side: "confederate" | "union";
  showImages: boolean;
}

const RosterContext = createContext<RosterContextValue | null>(null);

interface RosterProviderProps {
  children: ReactNode;
  gameId: string | undefined;
  side: "confederate" | "union";
  showImages: boolean;
}

export function RosterProvider({ children, gameId, side, showImages }: RosterProviderProps) {
  return (
    <RosterContext.Provider value={{ gameId, side, showImages }}>
      {children}
    </RosterContext.Provider>
  );
}

export function useRoster(): RosterContextValue {
  const context = useContext(RosterContext);
  if (!context) {
    throw new Error("useRoster must be used within a RosterProvider");
  }
  return context;
}

// Optional hook that doesn't throw - useful during transition
export function useRosterOptional(): RosterContextValue | null {
  return useContext(RosterContext);
}
