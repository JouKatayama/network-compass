"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState } from "react";

import type { PersonSearchResultSchema } from "../../lib/api/generated";
import { searchPeople } from "../../lib/api/people";

type PeopleSearchProps = {
  onSelect(result: PersonSearchResultSchema): void;
};

export function PeopleSearch({ onSelect }: PeopleSearchProps) {
  const listboxId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const timeout = window.setTimeout(() => setQuery(input.trim()), 180);
    return () => window.clearTimeout(timeout);
  }, [input]);

  const searchQuery = useQuery({
    enabled: query.length > 0,
    queryFn: ({ signal }) => searchPeople(query, signal),
    queryKey: ["people-search", query],
    staleTime: 30_000,
  });
  const results = searchQuery.data?.items ?? [];
  const clampedActiveIndex =
    results.length > 0
      ? Math.max(0, Math.min(activeIndex, results.length - 1))
      : -1;
  const activeOptionId = results[clampedActiveIndex]
    ? `${listboxId}-${clampedActiveIndex}`
    : undefined;

  const select = (result: PersonSearchResultSchema) => {
    setInput(result.person.displayName);
    inputRef.current?.focus();
    setOpen(false);
    onSelect(result);
  };

  return (
    <div className="people-search">
      <label htmlFor={`${listboxId}-input`}>人を検索</label>
      <div className="search-input-shell">
        <span aria-hidden="true">⌕</span>
        <input
          aria-activedescendant={open ? activeOptionId : undefined}
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-expanded={open && query.length > 0}
          autoComplete="off"
          id={`${listboxId}-input`}
          onChange={(event) => {
            setInput(event.target.value);
            setActiveIndex(-1);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(event) => {
            if (event.key === "ArrowDown") {
              event.preventDefault();
              setOpen(true);
              setActiveIndex((index) =>
                Math.min(index + 1, results.length - 1),
              );
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              setActiveIndex((index) => Math.max(index - 1, 0));
            } else if (event.key === "Enter" && results[clampedActiveIndex]) {
              event.preventDefault();
              select(results[clampedActiveIndex]);
            } else if (event.key === "Escape") {
              setOpen(false);
            }
          }}
          placeholder="名前・役割・スキルで検索"
          ref={inputRef}
          role="combobox"
          type="search"
          value={input}
        />
        {searchQuery.isFetching ? (
          <span aria-label="検索中" className="search-spinner" />
        ) : null}
      </div>
      {open && query.length > 0 ? (
        <div className="search-popover">
          {searchQuery.isError ? (
            <p role="alert">検索できませんでした。もう一度お試しください。</p>
          ) : null}
          {!searchQuery.isFetching &&
          !searchQuery.isError &&
          results.length === 0 ? (
            <p>一致する人が見つかりませんでした。</p>
          ) : null}
          {results.length > 0 ? (
            <ul aria-label="人の検索結果" id={listboxId} role="listbox">
              {results.map((result, index) => (
                <li
                  aria-selected={index === clampedActiveIndex}
                  id={`${listboxId}-${index}`}
                  key={result.person.personId}
                  onClick={() => select(result)}
                  onMouseDown={(event) => event.preventDefault()}
                  onMouseEnter={() => setActiveIndex(index)}
                  role="option"
                >
                  <span>
                    <b>{result.person.displayName}</b>
                    <small>
                      {[result.person.role, result.person.organization?.name]
                        .filter(Boolean)
                        .join(" · ") || "プロフィール情報は限定的です"}
                    </small>
                  </span>
                  <em>{result.relationshipLabel}</em>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
