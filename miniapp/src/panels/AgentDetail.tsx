import { useEffect, useRef, useState } from "react";
import {
  Avatar,
  Banner,
  Button,
  ButtonGroup,
  Cell,
  Div,
  File,
  FormItem,
  FormLayoutGroup,
  Group,
  Header,
  Input,
  Panel,
  PanelHeader,
  PanelHeaderBack,
  Placeholder,
  Separator,
  Spinner,
  Tabs,
  TabsItem,
  Textarea,
} from "@vkontakte/vkui";
import { Icon28AttachOutline, Icon28DocumentOutline, Icon24Delete } from "@vkontakte/icons";

import {
  chatWithAgent,
  deleteAgent,
  deleteKB,
  getAgent,
  listConversations,
  listKB,
  uploadKBFile,
  uploadKBManual,
  uploadKBUrl,
  type AgentRead,
  type ChatResponse,
  type ChatSource,
  type ConversationRead,
  type DocumentRead,
} from "@/api/client";

interface Props {
  id: string;
  agentId: string;
  onBack: () => void;
}

type Tab = "chat" | "knowledge" | "settings" | "history";

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  confidence?: number;
  cost?: string;
}

export function AgentDetail({ id, agentId, onBack }: Props) {
  const [agent, setAgent] = useState<AgentRead | null>(null);
  const [tab, setTab] = useState<Tab>("chat");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAgent(agentId)
      .then(setAgent)
      .finally(() => setLoading(false));
  }, [agentId]);

  async function handleDelete() {
    if (!agent) return;
    if (!confirm(`Удалить агента "${agent.name}" вместе с базой знаний?`)) return;
    await deleteAgent(agent.id);
    onBack();
  }

  return (
    <Panel id={id}>
      <PanelHeader before={<PanelHeaderBack onClick={onBack} />}>
        {agent?.name ?? "Агент"}
      </PanelHeader>

      {loading || !agent ? (
        <Spinner size="m" style={{ margin: 24 }} />
      ) : (
        <>
          <Tabs>
            <TabsItem selected={tab === "chat"} onClick={() => setTab("chat")}>
              Тест-чат
            </TabsItem>
            <TabsItem selected={tab === "knowledge"} onClick={() => setTab("knowledge")}>
              База знаний
            </TabsItem>
            <TabsItem selected={tab === "history"} onClick={() => setTab("history")}>
              Диалоги
            </TabsItem>
            <TabsItem selected={tab === "settings"} onClick={() => setTab("settings")}>
              Настройки
            </TabsItem>
          </Tabs>

          {tab === "chat" && <ChatTab agentId={agent.id} />}
          {tab === "knowledge" && <KnowledgeTab agentId={agent.id} />}
          {tab === "history" && <HistoryTab agentId={agent.id} />}
          {tab === "settings" && <SettingsTab agent={agent} onDelete={handleDelete} />}
        </>
      )}
    </Panel>
  );
}

// =============================================================================
function ChatTab({ agentId }: { agentId: string }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setSending(true);
    const userTurn: ChatTurn = { role: "user", content: text };
    setTurns((prev) => [...prev, userTurn]);
    setInput("");
    try {
      const resp: ChatResponse = await chatWithAgent(agentId, {
        message: text,
        history: turns.map((t) => ({ role: t.role, content: t.content })),
      });
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: resp.text,
          sources: resp.sources,
          confidence: resp.confidence,
          cost: resp.credits_spent,
        },
      ]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setTurns((prev) => [...prev, { role: "assistant", content: `⚠️ Ошибка: ${msg}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <Group>
      <Div style={{ maxHeight: 520, overflowY: "auto", paddingBottom: 8 }}>
        {turns.length === 0 && (
          <Placeholder>
            Напиши сообщение ниже — агент ответит, опираясь на свою базу знаний.
          </Placeholder>
        )}
        {turns.map((t, i) => (
          <div key={i} style={{ marginBottom: 12 }}>
            <Cell
              multiline
              before={
                <Avatar
                  size={32}
                  initials={t.role === "user" ? "Я" : "🤖"}
                  style={{
                    background:
                      t.role === "user" ? "var(--vkui--color_background_accent)" : undefined,
                  }}
                />
              }
              subtitle={
                t.role === "assistant" && t.cost
                  ? `${t.cost} кр · confidence ${(t.confidence ?? 0).toFixed(2)}`
                  : undefined
              }
            >
              {t.content}
            </Cell>
            {t.sources && t.sources.length > 0 && (
              <Div>
                <Header>Источники из базы знаний</Header>
                {t.sources.map((s, j) => (
                  <Banner key={j} mode="tint" title={`Релевантность ${s.score.toFixed(2)}`}>
                    {s.text.slice(0, 200)}
                    {s.text.length > 200 ? "…" : ""}
                  </Banner>
                ))}
              </Div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </Div>
      <Separator />
      <Div>
        <FormLayoutGroup>
          <Textarea
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Спроси что-нибудь у агента…"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <Button stretched size="l" onClick={send} loading={sending} disabled={!input.trim()}>
            Отправить
          </Button>
        </FormLayoutGroup>
      </Div>
    </Group>
  );
}

// =============================================================================
function KnowledgeTab({ agentId }: { agentId: string }) {
  const [docs, setDocs] = useState<DocumentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [url, setUrl] = useState("");
  const [manualTitle, setManualTitle] = useState("");
  const [manualText, setManualText] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => {
    setLoading(true);
    listKB(agentId)
      .then(setDocs)
      .finally(() => setLoading(false));
  };

  useEffect(load, [agentId]);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true);
    try {
      await uploadKBFile(agentId, f);
      load();
    } catch (err) {
      alert(`Ошибка: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleUrl() {
    if (!url.trim()) return;
    setBusy(true);
    try {
      await uploadKBUrl(agentId, url.trim());
      setUrl("");
      load();
    } catch (err) {
      alert(`Ошибка: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleManual() {
    if (!manualTitle.trim() || !manualText.trim()) return;
    setBusy(true);
    try {
      await uploadKBManual(agentId, manualTitle.trim(), manualText.trim());
      setManualTitle("");
      setManualText("");
      load();
    } catch (err) {
      alert(`Ошибка: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(docId: string) {
    if (!confirm("Удалить документ из базы знаний?")) return;
    await deleteKB(agentId, docId);
    load();
  }

  return (
    <>
      <Group header={<Header>Добавить документ</Header>}>
        <FormItem top="Файл (PDF / DOCX / TXT / CSV / MD)">
          <File before={<Icon28AttachOutline />} onChange={handleFile} disabled={busy}>
            Выбрать файл
          </File>
        </FormItem>
        <FormItem top="URL страницы">
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/about"
          />
        </FormItem>
        <FormItem>
          <Button onClick={handleUrl} loading={busy} disabled={!url.trim()}>
            Загрузить страницу
          </Button>
        </FormItem>
        <Separator />
        <FormItem top="Ручной ввод — название">
          <Input
            value={manualTitle}
            onChange={(e) => setManualTitle(e.target.value)}
            placeholder="Тарифы / FAQ / Условия доставки"
          />
        </FormItem>
        <FormItem top="Ручной ввод — текст">
          <Textarea
            rows={4}
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            placeholder="Текст знаний для агента…"
          />
        </FormItem>
        <FormItem>
          <Button
            onClick={handleManual}
            loading={busy}
            disabled={!manualTitle.trim() || !manualText.trim()}
          >
            Добавить
          </Button>
        </FormItem>
      </Group>

      <Group header={<Header>Документы ({docs.length})</Header>}>
        {loading ? (
          <Spinner size="m" />
        ) : docs.length === 0 ? (
          <Placeholder>Пока пусто. Добавь файл, URL или текст выше.</Placeholder>
        ) : (
          docs.map((d) => (
            <Cell
              key={d.id}
              before={<Icon28DocumentOutline />}
              subtitle={`${d.source_type} · ${d.chunks_count ?? "?"} чанков${
                d.indexed_at ? "" : " · индексируется…"
              }`}
              after={
                <Button
                  appearance="negative"
                  mode="tertiary"
                  before={<Icon24Delete />}
                  onClick={() => handleDelete(d.id)}
                />
              }
            >
              {d.file_name ?? d.source_url ?? "Документ"}
            </Cell>
          ))
        )}
      </Group>
    </>
  );
}

// =============================================================================
function HistoryTab({ agentId }: { agentId: string }) {
  const [items, setItems] = useState<ConversationRead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listConversations(agentId)
      .then(setItems)
      .finally(() => setLoading(false));
  }, [agentId]);

  if (loading) return <Spinner size="m" style={{ margin: 24 }} />;
  if (items.length === 0)
    return <Placeholder>Диалогов ещё нет — попробуй вкладку «Тест-чат».</Placeholder>;

  return (
    <Group>
      {items.map((c) => (
        <div key={c.id}>
          <Cell
            multiline
            subtitle={`${new Date(c.created_at).toLocaleString("ru")} · ${
              c.tokens_in ?? 0
            } in / ${c.tokens_out ?? 0} out · ${c.credits_spent ?? "0"} кр`}
          >
            {c.messages.length} сообщений
          </Cell>
          <Div>
            {c.messages.slice(0, 4).map((m, i) => (
              <Banner key={i} mode="tint" title={m.role === "user" ? "Пользователь" : "Агент"}>
                {String(m.content ?? "").slice(0, 200)}
              </Banner>
            ))}
            {c.messages.length > 4 && <Header>…ещё {c.messages.length - 4}</Header>}
          </Div>
        </div>
      ))}
    </Group>
  );
}

// =============================================================================
function SettingsTab({ agent, onDelete }: { agent: AgentRead; onDelete: () => void }) {
  return (
    <Group>
      <Cell subtitle="Имя">{agent.name}</Cell>
      <Cell subtitle="Роль">{agent.role}</Cell>
      <Cell subtitle="Провайдер LLM">
        {agent.llm_provider} {agent.llm_model && `· ${agent.llm_model}`}
      </Cell>
      <Cell subtitle="Temperature">{agent.temperature}</Cell>
      <Cell subtitle="Порог уверенности">{agent.confidence_threshold}</Cell>
      <Cell subtitle="System prompt" multiline>
        {agent.system_prompt ?? "—"}
      </Cell>
      <Div>
        <ButtonGroup mode="vertical" stretched>
          <Button size="l" stretched appearance="negative" onClick={onDelete}>
            Удалить агента
          </Button>
        </ButtonGroup>
      </Div>
    </Group>
  );
}
