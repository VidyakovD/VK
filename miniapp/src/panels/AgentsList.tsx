import { useEffect, useState } from "react";
import {
  Avatar,
  Button,
  ButtonGroup,
  Cell,
  CellButton,
  FormItem,
  FormLayoutGroup,
  Group,
  Input,
  ModalCard,
  ModalRoot,
  Panel,
  PanelHeader,
  PanelHeaderBack,
  Placeholder,
  Select,
  Spinner,
  Textarea,
} from "@vkontakte/vkui";
import { Icon28AddOutline, Icon24ChevronRight, Icon24LogoVk } from "@vkontakte/icons";

import {
  createAgent,
  listAgents,
  listCommunities,
  type AgentRead,
  type CommunityRead,
} from "@/api/client";

interface Props {
  id: string;
  onBack: () => void;
  onOpenAgent: (agentId: string) => void;
  onGoToCommunities: () => void;
}

const ROLE_LABELS: Record<string, string> = {
  consultant: "Консультант",
  sales: "Продавец",
  lead_qualifier: "Квалификатор лидов",
  support: "Поддержка",
};

export function AgentsList({ id, onBack, onOpenAgent, onGoToCommunities }: Props) {
  const [agents, setAgents] = useState<AgentRead[]>([]);
  const [communities, setCommunities] = useState<CommunityRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  // form state
  const [name, setName] = useState("");
  const [role, setRole] = useState("consultant");
  const [communityId, setCommunityId] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([listAgents(), listCommunities()])
      .then(([a, c]) => {
        setAgents(a);
        setCommunities(c);
        if (c.length > 0 && !communityId) setCommunityId(c[0].id);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  async function handleCreate() {
    if (!name.trim() || !communityId) return;
    setCreating(true);
    try {
      const a = await createAgent({
        community_id: communityId,
        name: name.trim(),
        role,
        system_prompt: systemPrompt.trim() || undefined,
        tone: "friendly",
        llm_provider: "openai",
      });
      setModalOpen(false);
      setName("");
      setSystemPrompt("");
      onOpenAgent(a.id);
    } catch (err) {
      alert(`Ошибка создания: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setCreating(false);
    }
  }

  return (
    <Panel id={id}>
      <PanelHeader before={<PanelHeaderBack onClick={onBack} />}>ИИ-агенты</PanelHeader>

      <Group>
        <CellButton
          before={<Icon28AddOutline />}
          onClick={() => {
            if (communities.length === 0) {
              alert("Сначала подключи сообщество — раздел «Сообщества»");
              return;
            }
            setModalOpen(true);
          }}
        >
          Создать агента
        </CellButton>
      </Group>

      {loading ? (
        <Spinner size="m" style={{ margin: 24 }} />
      ) : agents.length === 0 ? (
        <Placeholder
          action={
            communities.length === 0 ? (
              <Button onClick={onGoToCommunities}>К сообществам</Button>
            ) : undefined
          }
        >
          {communities.length === 0
            ? "Сначала подключи сообщество, потом создашь агента"
            : "Агентов пока нет. Создай первого выше."}
        </Placeholder>
      ) : (
        <Group>
          {agents.map((a) => (
            <Cell
              key={a.id}
              before={<Avatar size={40} initials={a.name[0]} />}
              subtitle={`${ROLE_LABELS[a.role] ?? a.role} · ${a.llm_provider}`}
              onClick={() => onOpenAgent(a.id)}
              after={<Icon24ChevronRight />}
            >
              {a.name}
            </Cell>
          ))}
        </Group>
      )}

      <ModalRoot activeModal={modalOpen ? "create-agent" : null}>
        <ModalCard
          id="create-agent"
          onClose={() => setModalOpen(false)}
          title="Новый ИИ-агент"
          icon={<Icon24LogoVk width={56} height={56} />}
          actions={
            <ButtonGroup mode="vertical" stretched>
              <Button
                size="l"
                stretched
                loading={creating}
                onClick={handleCreate}
                disabled={!name.trim() || !communityId}
              >
                Создать
              </Button>
            </ButtonGroup>
          }
        >
          <FormLayoutGroup>
            <FormItem top="Название" required>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Консультант магазина"
              />
            </FormItem>
            <FormItem top="Сообщество" required>
              <Select
                value={communityId}
                onChange={(e) => setCommunityId(e.target.value)}
                options={communities.map((c) => ({
                  label: c.group_name ?? `group_${c.vk_group_id}`,
                  value: c.id,
                }))}
              />
            </FormItem>
            <FormItem top="Роль">
              <Select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                options={[
                  { label: "Консультант", value: "consultant" },
                  { label: "Продавец", value: "sales" },
                  { label: "Квалификатор лидов", value: "lead_qualifier" },
                  { label: "Поддержка", value: "support" },
                ]}
              />
            </FormItem>
            <FormItem
              top="System prompt"
              bottom="Опционально: задай характер агента (например: «Ты — продавец фитнес-курса»)"
            >
              <Textarea
                rows={3}
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Ты — дружелюбный консультант…"
              />
            </FormItem>
          </FormLayoutGroup>
        </ModalCard>
      </ModalRoot>
    </Panel>
  );
}
