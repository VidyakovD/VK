import { useEffect, useState } from "react";
import {
  Avatar,
  Cell,
  Group,
  Header,
  Panel,
  PanelHeader,
  Placeholder,
  SimpleCell,
  Spinner,
} from "@vkontakte/vkui";
import {
  Icon28MessageOutline,
  Icon28PictureOutline,
  Icon28RobotOutline,
  Icon28StatisticsOutline,
  Icon28UsersOutline,
  Icon28WalletOutline,
} from "@vkontakte/icons";

import { getBalance, type BalanceRead } from "@/api/client";
import { useAuthStore } from "@/store/auth";

interface Props {
  id: string;
  onNavigate: (panel: string) => void;
}

export function Dashboard({ id, onNavigate }: Props) {
  const { user } = useAuthStore();
  const [balance, setBalance] = useState<BalanceRead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBalance()
      .then(setBalance)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Panel id={id}>
      <PanelHeader>Кабинет</PanelHeader>
      {!user ? (
        <Placeholder>Загружаю профиль…</Placeholder>
      ) : (
        <>
          <Group>
            <Cell
              before={<Avatar src={user.avatar_url ?? undefined} size={48} />}
              subtitle={
                loading
                  ? "загрузка…"
                  : `${balance?.credits_balance ?? "—"} кредитов`
              }
            >
              {user.first_name} {user.last_name}
            </Cell>
          </Group>

          <Group header={<Header>Модули</Header>}>
            <SimpleCell
              before={<Icon28UsersOutline />}
              onClick={() => onNavigate("communities")}
              subtitle="Подключить сообщество ВК"
            >
              Сообщества
            </SimpleCell>
            <SimpleCell
              before={<Icon28RobotOutline />}
              onClick={() => onNavigate("agents")}
              subtitle="ИИ-консультанты с базой знаний"
            >
              ИИ-агенты
            </SimpleCell>
            <SimpleCell
              before={<Icon28MessageOutline />}
              onClick={() => onNavigate("bots")}
              subtitle="Скоро"
              style={{ opacity: 0.5 }}
            >
              Чат-боты
            </SimpleCell>
            <SimpleCell
              before={<Icon28StatisticsOutline />}
              onClick={() => onNavigate("mailings")}
              subtitle="Скоро"
              style={{ opacity: 0.5 }}
            >
              Рассылки
            </SimpleCell>
            <SimpleCell
              before={<Icon28PictureOutline />}
              onClick={() => onNavigate("content")}
              subtitle="Скоро"
              style={{ opacity: 0.5 }}
            >
              Оформление сообщества
            </SimpleCell>
            <SimpleCell
              before={<Icon28WalletOutline />}
              onClick={() => onNavigate("billing")}
              subtitle="История транзакций и тарифы"
            >
              Баланс и тарифы
            </SimpleCell>
          </Group>

          {loading && <Spinner size="m" style={{ margin: 12 }} />}
        </>
      )}
    </Panel>
  );
}
