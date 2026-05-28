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
  Spinner,
  Snackbar,
} from "@vkontakte/vkui";
import { Icon28AddOutline, Icon24Delete, Icon16Done } from "@vkontakte/icons";

import {
  createCommunity,
  deleteCommunity,
  listCommunities,
  type CommunityRead,
} from "@/api/client";

interface Props {
  id: string;
  onBack: () => void;
}

export function Communities({ id, onBack }: Props) {
  const [items, setItems] = useState<CommunityRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [groupName, setGroupName] = useState("");
  const [groupId, setGroupId] = useState("");
  const [creating, setCreating] = useState(false);
  const [snack, setSnack] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    listCommunities()
      .then(setItems)
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  async function handleCreate() {
    if (!groupName.trim() || !groupId.trim()) return;
    setCreating(true);
    try {
      await createCommunity({
        vk_group_id: Number(groupId),
        group_name: groupName.trim(),
      });
      setModalOpen(false);
      setGroupName("");
      setGroupId("");
      setSnack("Сообщество добавлено");
      load();
    } catch (err) {
      setSnack(`Ошибка: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(community_id: string) {
    if (!confirm("Удалить сообщество вместе с агентами и базой знаний?")) return;
    try {
      await deleteCommunity(community_id);
      setSnack("Сообщество удалено");
      load();
    } catch (err) {
      setSnack(`Ошибка: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return (
    <Panel id={id}>
      <PanelHeader before={<PanelHeaderBack onClick={onBack} />}>Сообщества</PanelHeader>

      <Group>
        <CellButton before={<Icon28AddOutline />} onClick={() => setModalOpen(true)}>
          Добавить сообщество
        </CellButton>
      </Group>

      {loading ? (
        <Spinner size="m" style={{ margin: 24 }} />
      ) : items.length === 0 ? (
        <Placeholder>
          Пока ни одного сообщества не подключено. Нажми «Добавить» выше.
        </Placeholder>
      ) : (
        <Group>
          {items.map((c) => (
            <Cell
              key={c.id}
              before={<Avatar size={40} initials={c.group_name?.[0] ?? "?"} />}
              subtitle={`vk_group_id: ${c.vk_group_id}`}
              after={
                <Button
                  appearance="negative"
                  mode="tertiary"
                  before={<Icon24Delete />}
                  onClick={() => handleDelete(c.id)}
                />
              }
            >
              {c.group_name}
            </Cell>
          ))}
        </Group>
      )}

      <ModalRoot activeModal={modalOpen ? "create-community" : null}>
        <ModalCard
          id="create-community"
          onClose={() => setModalOpen(false)}
          header="Подключение сообщества"
          subheader="В dev-режиме без OAuth — указываешь любой ID и название"
          actions={
            <ButtonGroup mode="vertical" stretched>
              <Button
                size="l"
                stretched
                loading={creating}
                onClick={handleCreate}
                disabled={!groupName.trim() || !groupId.trim()}
              >
                Подключить
              </Button>
            </ButtonGroup>
          }
        >
          <FormLayoutGroup>
            <FormItem top="Название" required>
              <Input
                placeholder="Моя группа"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
              />
            </FormItem>
            <FormItem top="vk_group_id" required>
              <Input
                type="number"
                placeholder="12345"
                value={groupId}
                onChange={(e) => setGroupId(e.target.value)}
              />
            </FormItem>
          </FormLayoutGroup>
        </ModalCard>
      </ModalRoot>

      {snack && (
        <Snackbar
          onClose={() => setSnack(null)}
          before={<Icon16Done fill="var(--vkui--color_icon_positive)" />}
        >
          {snack}
        </Snackbar>
      )}
    </Panel>
  );
}
