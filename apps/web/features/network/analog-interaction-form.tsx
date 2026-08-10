"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from "react";

import type {
  DurationBucket,
  InteractionCaptureRequestSchema,
  PersonIdentitySchema,
} from "../../lib/api/generated";
import { captureInteraction } from "../../lib/api/interactions";

type AnalogType = InteractionCaptureRequestSchema["type"];

const TYPE_OPTIONS: ReadonlyArray<{ label: string; value: AnalogType }> = [
  { label: "オフィスで会話", value: "OFFICE_CHAT" },
  { label: "コーヒー", value: "COFFEE" },
  { label: "ランチ", value: "LUNCH" },
  { label: "ディナー", value: "DINNER" },
  { label: "コミュニティ", value: "COMMUNITY" },
  { label: "アクティビティ", value: "ACTIVITY" },
  { label: "その他", value: "OTHER" },
];

const DURATION_OPTIONS: ReadonlyArray<{
  label: string;
  value: DurationBucket;
}> = [
  { label: "少し", value: "SHORT" },
  { label: "しっかり", value: "MEDIUM" },
  { label: "長く", value: "LONG" },
];

function toLocalDateTimeInput(date: Date): string {
  const offsetMilliseconds = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMilliseconds)
    .toISOString()
    .slice(0, 16);
}

type AnalogInteractionFormProps = {
  onCancel(): void;
  onCaptured(): Promise<void>;
  person: PersonIdentitySchema;
};

export function AnalogInteractionForm({
  onCancel,
  onCaptured,
  person,
}: AnalogInteractionFormProps) {
  const queryClient = useQueryClient();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const typeErrorId = useId();
  const durationErrorId = useId();
  const dateErrorId = useId();
  const formErrorId = useId();
  const openedAt = useMemo(() => new Date(), []);
  const clientRequestId = useMemo(() => crypto.randomUUID(), []);
  const [type, setType] = useState<AnalogType | "">("");
  const [duration, setDuration] = useState<DurationBucket | "">("");
  const [occurredAt, setOccurredAt] = useState(() =>
    toLocalDateTimeInput(openedAt),
  );
  const [submitted, setSubmitted] = useState(false);

  const earliestOccurredAt = useMemo(() => {
    const earliest = new Date(openedAt);
    earliest.setDate(earliest.getDate() - 30);
    return toLocalDateTimeInput(earliest);
  }, [openedAt]);
  const latestOccurredAt = toLocalDateTimeInput(new Date());

  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  const mutation = useMutation({
    mutationFn: (request: InteractionCaptureRequestSchema) =>
      captureInteraction(request),
    onSuccess: async () => {
      await queryClient.refetchQueries({
        exact: true,
        queryKey: ["person-detail", person.personId],
      });
      await onCaptured();
    },
  });

  const typeInvalid = submitted && !type;
  const durationInvalid = submitted && !duration;
  const selectedDate = new Date(occurredAt);
  const dateOutOfRange =
    !occurredAt ||
    Number.isNaN(selectedDate.getTime()) ||
    selectedDate < new Date(earliestOccurredAt) ||
    selectedDate > new Date();
  const dateInvalid = submitted && dateOutOfRange;

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitted(true);
    mutation.reset();
    if (!type || !duration || dateOutOfRange) return;

    mutation.mutate({
      clientRequestId,
      durationBucket: duration,
      occurredAt: selectedDate.toISOString(),
      otherPersonId: person.personId,
      type,
    });
  };

  return (
    <div className="capture-content">
      <button className="capture-back" onClick={onCancel} type="button">
        <span aria-hidden="true">←</span> 詳細へ戻る
      </button>
      <header className="capture-heading">
        <p>ANALOG CONTACT</p>
        <h2 id="person-detail-title" ref={headingRef} tabIndex={-1}>
          接点を記録
        </h2>
        <span>{person.displayName}</span>
      </header>

      <form className="capture-form" noValidate onSubmit={submit}>
        <fieldset
          aria-describedby={typeInvalid ? typeErrorId : undefined}
          aria-invalid={typeInvalid}
        >
          <legend>どんな接点でしたか？</legend>
          <div className="capture-options capture-type-options">
            {TYPE_OPTIONS.map((option) => (
              <label key={option.value}>
                <input
                  checked={type === option.value}
                  disabled={mutation.isPending}
                  name="interaction-type"
                  onChange={() => setType(option.value)}
                  type="radio"
                  value={option.value}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
          {typeInvalid ? (
            <p className="capture-field-error" id={typeErrorId}>
              接点の種類を選んでください。
            </p>
          ) : null}
        </fieldset>

        <fieldset
          aria-describedby={durationInvalid ? durationErrorId : undefined}
          aria-invalid={durationInvalid}
        >
          <legend>どのくらい話しましたか？</legend>
          <div className="capture-options capture-duration-options">
            {DURATION_OPTIONS.map((option) => (
              <label key={option.value}>
                <input
                  checked={duration === option.value}
                  disabled={mutation.isPending}
                  name="interaction-duration"
                  onChange={() => setDuration(option.value)}
                  type="radio"
                  value={option.value}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
          {durationInvalid ? (
            <p className="capture-field-error" id={durationErrorId}>
              時間の長さを選んでください。
            </p>
          ) : null}
        </fieldset>

        <label
          aria-describedby={dateInvalid ? dateErrorId : undefined}
          className="capture-date"
        >
          <span>いつの接点ですか？</span>
          <input
            disabled={mutation.isPending}
            max={latestOccurredAt}
            min={earliestOccurredAt}
            onChange={(event) => setOccurredAt(event.target.value)}
            required
            type="datetime-local"
            value={occurredAt}
          />
          <small>現在時刻を入れています。必要なときだけ変更できます。</small>
        </label>
        {dateInvalid ? (
          <p className="capture-field-error" id={dateErrorId}>
            30日前から現在までの日時を指定してください。
          </p>
        ) : null}

        {mutation.isError ? (
          <p className="capture-submit-error" id={formErrorId} role="alert">
            保存できませんでした。入力内容を保ったまま、もう一度お試しください。
          </p>
        ) : null}

        <button
          aria-describedby={mutation.isError ? formErrorId : undefined}
          className="capture-save"
          disabled={mutation.isPending}
          type="submit"
        >
          {mutation.isPending ? "保存しています…" : "この接点を保存"}
        </button>
      </form>
    </div>
  );
}
