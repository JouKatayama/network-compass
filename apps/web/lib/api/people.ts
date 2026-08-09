import type { PersonDetailSchema, PersonSearchPageSchema } from "./generated";

export class PeopleRequestError extends Error {
  constructor() {
    super("People request failed");
    this.name = "PeopleRequestError";
  }
}

async function readPeopleResponse<T>(
  input: RequestInfo | URL,
  signal?: AbortSignal,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, {
      headers: { Accept: "application/json" },
      signal,
    });
  } catch {
    throw new PeopleRequestError();
  }
  if (!response.ok) throw new PeopleRequestError();
  return (await response.json()) as T;
}

export function fetchPersonDetail(
  personId: string,
  signal?: AbortSignal,
): Promise<PersonDetailSchema> {
  return readPeopleResponse<PersonDetailSchema>(
    `/api/people/${encodeURIComponent(personId)}`,
    signal,
  );
}

export function searchPeople(
  query: string,
  signal?: AbortSignal,
): Promise<PersonSearchPageSchema> {
  const params = new URLSearchParams({ limit: "8", q: query });
  return readPeopleResponse<PersonSearchPageSchema>(
    `/api/people/search?${params}`,
    signal,
  );
}
