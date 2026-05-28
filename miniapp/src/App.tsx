import { useEffect, useState } from "react";
import {
  SplitLayout,
  SplitCol,
  View,
  Panel,
  PanelHeader,
  Group,
  Header,
  SimpleCell,
  Spinner,
  Placeholder,
  Avatar,
  Cell,
} from "@vkontakte/vkui";
import {
  Icon28RobotOutline,
  Icon28MessageOutline,
  Icon28ChartOutline,
  Icon28PictureOutline,
  Icon28UsersOutline,
  Icon28WalletOutline,
} from "@vkontakte/icons";

import { authVK, getMe } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import { getLaunchParams } from "@/lib/vkBridge";

type ActivePanel =
  | "dashboard"
  | "communities"
  | "bots"
  | "mailings"
  | "agents"
  | "content"
  | "billing";

export function App() {
  const { user, setTokens, setUser } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<ActivePanel>("dashboard");

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
      <Placeholder header="Не удалось войти" action={authError}>
        Открой Mini App из ВКонтакте, либо настрой VITE_MOCK_LAUNCH_PARAMS=true в .env
      </Placeholder>
    );
  }

  return (
    <SplitLayout header={<PanelHeader delimiter="none" />}>
      <SplitCol autoSpaced>
        <View activePanel={activePanel} id="main">
          <Panel id="dashboard">
            <PanelHeader>Кабинет</PanelHeader>
            {user && (
              <Group>
                <Cell
                  before={<Avatar src={user.avatar_url ?? undefined} size={48} />}
                  subtitle={`Баланс: ${user.credits_balance} кр.`}
                >
                  {user.first_name} {user.last_name}
                </Cell>
              </Group>
            )}
            <Group header={<Header>Модули</Header>}>
              <SimpleCell
                before={<Icon28UsersOutline />}
                onClick={() => setActivePanel("communities")}
              >
                Сообщества
              </SimpleCell>
              <SimpleCell
                before={<Icon28MessageOutline />}
                onClick={() => setActivePanel("bots")}
              >
                Чат-боты
              </SimpleCell>
              <SimpleCell
                before={<Icon28ChartOutline />}
                onClick={() => setActivePanel("mailings")}
              >
                Рассылки
              </SimpleCell>
              <SimpleCell
                before={<Icon28RobotOutline />}
                onClick={() => setActivePanel("agents")}
              >
                ИИ-агенты
              </SimpleCell>
              <SimpleCell
                before={<Icon28PictureOutline />}
                onClick={() => setActivePanel("content")}
              >
                Оформление сообщества
              </SimpleCell>
              <SimpleCell
                before={<Icon28WalletOutline />}
                onClick={() => setActivePanel("billing")}
              >
                Баланс и тарифы
              </SimpleCell>
            </Group>
          </Panel>

          <Panel id="communities">
            <PanelHeader before={<BackButton onClick={() => setActivePanel("dashboard")} />}>
              Сообщества
            </PanelHeader>
            <Placeholder>Подключение сообществ — в разработке</Placeholder>
          </Panel>
          <Panel id="bots">
            <PanelHeader before={<BackButton onClick={() => setActivePanel("dashboard")} />}>
              Чат-боты
            </PanelHeader>
            <Placeholder>Нодовый редактор — в разработке</Placeholder>
          </Panel>
          <Panel id="mailings">
            <PanelHeader before={<BackButton onClick={() => setActivePanel("dashboard")} />}>
              Рассылки
            </PanelHeader>
            <Placeholder>Рассылки — в разработке</Placeholder>
          </Panel>
          <Panel id="agents">
            <PanelHeader before={<BackButton onClick={() => setActivePanel("dashboard")} />}>
              ИИ-агенты
            </PanelHeader>
            <Placeholder>Создание агента и базы знаний — в разработке</Placeholder>
          </Panel>
          <Panel id="content">
            <PanelHeader before={<BackButton onClick={() => setActivePanel("dashboard")} />}>
              Оформление сообщества
            </PanelHeader>
            <Placeholder>Генерация постов и картинок — в разработке</Placeholder>
          </Panel>
          <Panel id="billing">
            <PanelHeader before={<BackButton onClick={() => setActivePanel("dashboard")} />}>
              Баланс и тарифы
            </PanelHeader>
            <Placeholder>Биллинг — в разработке</Placeholder>
          </Panel>
        </View>
      </SplitCol>
    </SplitLayout>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{ background: "none", border: "none", cursor: "pointer", padding: "8px 12px" }}
      aria-label="Назад"
    >
      ←
    </button>
  );
}
