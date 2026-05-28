import { useEffect, useState } from "react";
import {
  Panel,
  PanelHeader,
  Placeholder,
  SplitCol,
  SplitLayout,
  Spinner,
  View,
} from "@vkontakte/vkui";

import { authVK, getMe } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import { getLaunchParams } from "@/lib/vkBridge";

import { AgentDetail } from "@/panels/AgentDetail";
import { AgentsList } from "@/panels/AgentsList";
import { Billing } from "@/panels/Billing";
import { Communities } from "@/panels/Communities";
import { Dashboard } from "@/panels/Dashboard";

type ActivePanel =
  | "dashboard"
  | "communities"
  | "agents"
  | "agent_detail"
  | "billing"
  | "bots"
  | "mailings"
  | "content";

export function App() {
  const { setTokens, setUser } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<ActivePanel>("dashboard");
  const [openedAgentId, setOpenedAgentId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const launchParams = await getLaunchParams();
        const tokens = await authVK(launchParams);
        if (cancelled) return;
        setTokens(tokens.access_token, tokens.refresh_token);
        const me = await getMe();
        if (cancelled) return;
        setUser(me);
      } catch (err) {
        if (!cancelled) setAuthError(err instanceof Error ? err.message : "Auth failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setTokens, setUser]);

  if (loading) {
    return <Spinner size="l" style={{ margin: "64px auto" }} />;
  }

  if (authError) {
    return (
      <Placeholder title="Не удалось войти" action={authError}>
        Открой Mini App из ВКонтакте, либо в dev-режиме поставь VITE_MOCK_LAUNCH_PARAMS=true.
      </Placeholder>
    );
  }

  function openAgent(id: string) {
    setOpenedAgentId(id);
    setActivePanel("agent_detail");
  }

  return (
    <SplitLayout header={<PanelHeader delimiter="none" />}>
      <SplitCol autoSpaced>
        <View activePanel={activePanel} id="main">
          <Dashboard id="dashboard" onNavigate={(p) => setActivePanel(p as ActivePanel)} />
          <Communities id="communities" onBack={() => setActivePanel("dashboard")} />
          <AgentsList
            id="agents"
            onBack={() => setActivePanel("dashboard")}
            onOpenAgent={openAgent}
            onGoToCommunities={() => setActivePanel("communities")}
          />
          <AgentDetail
            id="agent_detail"
            agentId={openedAgentId ?? ""}
            onBack={() => setActivePanel("agents")}
          />
          <Billing id="billing" onBack={() => setActivePanel("dashboard")} />

          {/* Placeholders for future stages */}
          <Panel id="bots">
            <PanelHeader>Чат-боты</PanelHeader>
            <Placeholder>Нодовый редактор сценариев — Этап 3 (в разработке)</Placeholder>
          </Panel>
          <Panel id="mailings">
            <PanelHeader>Рассылки</PanelHeader>
            <Placeholder>Сегментированные рассылки — Этап 4 (в разработке)</Placeholder>
          </Panel>
          <Panel id="content">
            <PanelHeader>Оформление сообщества</PanelHeader>
            <Placeholder>Генерация постов, обложек, контент-план — Этап 5 (в разработке)</Placeholder>
          </Panel>
        </View>
      </SplitCol>
    </SplitLayout>
  );
}
