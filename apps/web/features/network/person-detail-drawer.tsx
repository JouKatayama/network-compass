"use client";

import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type {
  NamedContextSchema,
  PersonDetailSchema,
  PersonIdentitySchema,
} from "../../lib/api/generated";
import { fetchPersonDetail } from "../../lib/api/people";
import { AnalogInteractionForm } from "./analog-interaction-form";

type PersonDetailDrawerProps = {
  expanded: boolean;
  expansionError: boolean;
  expanding: boolean;
  onClose(): void;
  onDetail(detail: PersonDetailSchema | null): void;
  onExpand(): void;
  onInteractionCaptured(): Promise<void>;
  personId: string;
  personNameById: ReadonlyMap<string, string>;
};

function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  return new Intl.DateTimeFormat("ja-JP", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  return words
    .slice(-2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function IdentityAvatar({ person }: { person: PersonIdentitySchema }) {
  return (
    <div
      aria-label={
        person.avatarUrl
          ? `${person.displayName}のプロフィール画像`
          : "プロフィール画像なし"
      }
      className="detail-avatar"
      style={
        person.avatarUrl
          ? { backgroundImage: `url(${person.avatarUrl})` }
          : undefined
      }
    >
      <span>{initials(person.displayName)}</span>
    </div>
  );
}

function ContextList({
  items,
  title,
}: {
  items?: NamedContextSchema[];
  title: string;
}) {
  if (!items?.length) return null;
  return (
    <section className="detail-section">
      <h3>{title}</h3>
      <ul className="context-chips">
        {items.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </section>
  );
}

export function PersonDetailDrawer({
  expanded,
  expansionError,
  expanding,
  onClose,
  onDetail,
  onExpand,
  onInteractionCaptured,
  personId,
  personNameById,
}: PersonDetailDrawerProps) {
  const drawerRef = useRef<HTMLElement>(null);
  const captureButtonRef = useRef<HTMLButtonElement>(null);
  const [capturing, setCapturing] = useState(false);
  const [captureStatus, setCaptureStatus] = useState("");
  const detailQuery = useQuery({
    queryFn: ({ signal }) => fetchPersonDetail(personId, signal),
    queryKey: ["person-detail", personId],
  });

  useEffect(() => {
    drawerRef.current?.focus();
  }, [personId]);

  useEffect(() => {
    onDetail(detailQuery.data ?? null);
    return () => onDetail(null);
  }, [detailQuery.data, onDetail]);

  const cancelCapture = useCallback(() => {
    setCapturing(false);
    setCaptureStatus("");
    window.setTimeout(() => captureButtonRef.current?.focus(), 0);
  }, []);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (capturing) cancelCapture();
      else onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [cancelCapture, capturing, onClose]);

  const finishCapture = useCallback(async () => {
    await onInteractionCaptured();
    setCapturing(false);
    setCaptureStatus(
      `${detailQuery.data?.person.displayName ?? "選択した人"}との接点を保存しました。詳細とネットワークを更新しました。`,
    );
    window.setTimeout(() => drawerRef.current?.focus(), 0);
  }, [detailQuery.data?.person.displayName, onInteractionCaptured]);

  const pathLabels = useMemo(
    () =>
      (detailQuery.data?.connectionPaths[0] ?? []).map(
        (pathPersonId) =>
          personNameById.get(pathPersonId) ??
          (pathPersonId === detailQuery.data?.person.personId
            ? detailQuery.data.person.displayName
            : "つながりのある人"),
      ),
    [detailQuery.data, personNameById],
  );

  return (
    <aside
      aria-label={detailQuery.data ? undefined : "人物詳細"}
      aria-labelledby={detailQuery.data ? "person-detail-title" : undefined}
      className="person-drawer"
      ref={drawerRef}
      role="dialog"
      tabIndex={-1}
    >
      <button
        aria-label="詳細を閉じる"
        className="drawer-close"
        onClick={onClose}
        type="button"
      >
        ×
      </button>
      {detailQuery.isPending ? (
        <div aria-busy="true" className="detail-loading">
          <span />
          <p>この人とのつながりを読み込んでいます</p>
        </div>
      ) : null}
      {detailQuery.isError ? (
        <div className="detail-error" role="alert">
          <h2 id="person-detail-title">詳細を表示できませんでした</h2>
          <p>接続を確認して、もう一度お試しください。</p>
          <button onClick={() => void detailQuery.refetch()} type="button">
            再読み込み
          </button>
        </div>
      ) : null}
      {detailQuery.data && capturing ? (
        <AnalogInteractionForm
          onCancel={cancelCapture}
          onCaptured={finishCapture}
          person={detailQuery.data.person}
        />
      ) : null}
      {detailQuery.data && !capturing ? (
        <div className="detail-content">
          <header className="detail-identity">
            <IdentityAvatar person={detailQuery.data.person} />
            <div>
              <p>
                {detailQuery.data.relationship.connectionType === "TWO_HOP"
                  ? "POTENTIAL CONNECTION"
                  : "YOUR CONNECTION"}
              </p>
              <h2 id="person-detail-title">
                {detailQuery.data.person.displayName}
              </h2>
              <span>
                {[
                  detailQuery.data.person.role,
                  detailQuery.data.person.organization?.name,
                  detailQuery.data.person.location,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </span>
            </div>
          </header>

          <section className="relationship-summary">
            <span
              className={`relationship-badge relationship-${detailQuery.data.relationship.state?.toLowerCase() ?? "potential"}`}
            >
              {detailQuery.data.relationship.label}
            </span>
            {detailQuery.data.relationship.lastContactAt ? (
              <p>
                最後に確認できた接点{" "}
                <b>{formatDate(detailQuery.data.relationship.lastContactAt)}</b>
              </p>
            ) : null}
            {detailQuery.data.relationship.historyNote ? (
              <p>{detailQuery.data.relationship.historyNote}</p>
            ) : null}
          </section>

          {pathLabels.length > 1 ? (
            <section className="detail-section connection-path">
              <h3>つながり方</h3>
              <ol>
                {pathLabels.map((label, index) => (
                  <li key={`${label}-${index}`}>{label}</li>
                ))}
              </ol>
            </section>
          ) : null}

          <section className="detail-section timeline-section">
            <h3>関係の記憶</h3>
            {detailQuery.data.timeline.length > 0 ? (
              <ol className="timeline-list">
                {detailQuery.data.timeline.map((item, index) => (
                  <li key={`${item.itemType}-${item.occurredAt}-${index}`}>
                    <span />
                    <div>
                      <time>{formatDate(item.occurredAt)}</time>
                      <b>{item.title}</b>
                      {item.context ? <small>{item.context.name}</small> : null}
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="limited-history">
                {detailQuery.data.relationship.connectionType === "TWO_HOP"
                  ? "まだ直接話した記録はありません。共有されている文脈だけを表示しています。"
                  : "確認できる履歴はまだ多くありません。分かっている事実だけを表示しています。"}
              </p>
            )}
          </section>

          {detailQuery.data.commonContext.mutualConnections?.length ? (
            <section className="detail-section">
              <h3>共通のつながり</h3>
              <ul className="mutual-list">
                {detailQuery.data.commonContext.mutualConnections.map(
                  (person) => (
                    <li key={person.personId}>
                      {person.displayName}
                      <small>{person.role}</small>
                    </li>
                  ),
                )}
              </ul>
            </section>
          ) : null}
          <ContextList
            items={detailQuery.data.commonContext.projects}
            title="共通のプロジェクト"
          />
          <ContextList
            items={detailQuery.data.commonContext.communities}
            title="共通のコミュニティ"
          />
          <ContextList
            items={detailQuery.data.commonContext.activities}
            title="共通のアクティビティ"
          />
          <ContextList
            items={detailQuery.data.commonContext.skills}
            title="共通のスキル"
          />

          {expansionError ? (
            <p className="expansion-error" role="alert">
              つながりを広げられませんでした。もう一度お試しください。
            </p>
          ) : null}

          <button
            className="capture-interaction-button"
            onClick={() => {
              setCaptureStatus("");
              setCapturing(true);
            }}
            ref={captureButtonRef}
            type="button"
          >
            <span>
              <b>接点を記録</b>
              <small>実際に話したことを追加</small>
            </span>
            <span aria-hidden="true">＋</span>
          </button>

          <button
            className="expand-connections-button"
            disabled={expanded || expanding}
            onClick={onExpand}
            type="button"
          >
            {expanding
              ? "つながりを広げています…"
              : expanded
                ? "この人から展開済み"
                : "この人からつながりを広げる"}
            <span aria-hidden="true">＋</span>
          </button>
        </div>
      ) : null}
      <p aria-live="polite" className="sr-only" role="status">
        {captureStatus}
      </p>
    </aside>
  );
}
