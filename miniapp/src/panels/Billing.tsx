import { useEffect, useState } from "react";
import {
  Banner,
  Cell,
  Group,
  Header,
  Panel,
  PanelHeader,
  PanelHeaderBack,
  Placeholder,
  Spinner,
} from "@vkontakte/vkui";

import {
  getBalance,
  listPricing,
  listTransactions,
  type BalanceRead,
  type PricingRuleRead,
  type TransactionRead,
} from "@/api/client";

interface Props {
  id: string;
  onBack: () => void;
}

export function Billing({ id, onBack }: Props) {
  const [balance, setBalance] = useState<BalanceRead | null>(null);
  const [txns, setTxns] = useState<TransactionRead[]>([]);
  const [pricing, setPricing] = useState<PricingRuleRead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getBalance(), listTransactions(50), listPricing()])
      .then(([b, t, p]) => {
        setBalance(b);
        setTxns(t);
        setPricing(p);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <Panel id={id}>
      <PanelHeader before={<PanelHeaderBack onClick={onBack} />}>Баланс и тарифы</PanelHeader>

      {loading ? (
        <Spinner size="m" style={{ margin: 24 }} />
      ) : (
        <>
          <Group>
            <Banner
              mode="image"
              header={`${balance?.credits_balance ?? "0"} кредитов`}
              subheader={
                balance?.trial_ends_at
                  ? `Триал до ${new Date(balance.trial_ends_at).toLocaleDateString("ru")}`
                  : "Триал завершён"
              }
              background={
                <div
                  style={{
                    background:
                      "linear-gradient(135deg, var(--vkui--color_background_accent), #4a76a8)",
                  }}
                />
              }
            />
          </Group>

          <Group header={<Header>История транзакций ({txns.length})</Header>}>
            {txns.length === 0 ? (
              <Placeholder>Транзакций ещё нет.</Placeholder>
            ) : (
              txns.map((t) => (
                <Cell
                  key={t.id}
                  subtitle={`${new Date(t.created_at).toLocaleString("ru")}${
                    t.resource_type ? ` · ${t.resource_type}` : ""
                  }`}
                  after={
                    <span
                      style={{
                        color: parseFloat(t.amount) < 0 ? "#e74c3c" : "#27ae60",
                        fontWeight: 600,
                      }}
                    >
                      {parseFloat(t.amount) > 0 ? "+" : ""}
                      {t.amount} кр
                    </span>
                  }
                  multiline
                >
                  {t.description ?? t.type}
                </Cell>
              ))
            )}
          </Group>

          <Group header={<Header>Текущие тарифы</Header>}>
            {pricing.map((p) => (
              <Cell key={p.resource_type} subtitle={p.resource_type} after={`${p.credits_cost} кр`}>
                {p.description ?? p.resource_type}
              </Cell>
            ))}
          </Group>
        </>
      )}
    </Panel>
  );
}
