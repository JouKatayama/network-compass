"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useRef, useState, type ReactNode } from "react";

import type { GraphProjectionSchema } from "../../lib/api/generated";
import { fetchNetworkProjection } from "../../lib/api/network";
import { buildNetworkGraph } from "./graph/build-network-graph";
import { NetworkGraphCanvas } from "./graph/network-graph-canvas";
import type { NetworkGraphController, VisibleHopMode } from "./graph/types";

function CompassMark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 32 32">
      <circle cx="16" cy="16" fill="none" r="11.5" />
      <path d="m19.5 12.5-2.1 4.9-4.9 2.1 2.1-4.9 4.9-2.1Z" />
    </svg>
  );
}

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg aria-hidden="true" fill="none" viewBox="0 0 24 24">
      {children}
    </svg>
  );
}

function AppRail() {
  return (
    <aside aria-label="メインナビゲーション" className="app-rail">
      <div className="brand-mark" title="Network Compass">
        <CompassMark />
      </div>
      <nav>
        <a aria-current="page" className="rail-link" href="/network">
          <Icon>
            <circle cx="12" cy="8" r="3" />
            <circle cx="6" cy="17" r="2.4" />
            <circle cx="18" cy="17" r="2.4" />
            <path d="m10.2 10.4-2.6 4.2m6.2-4.2 2.6 4.2M8.4 17h7.2" />
          </Icon>
          <span>My Network</span>
        </a>
      </nav>
      <div aria-label="開発用ペルソナ P001" className="persona-avatar">
        <span>MN</span>
      </div>
    </aside>
  );
}

function NetworkLoading() {
  return (
    <div
      aria-busy="true"
      aria-label="ネットワークを読み込み中"
      className="graph-state loading-state"
    >
      <div className="loading-orbit">
        <span />
        <span />
        <span />
        <span />
      </div>
      <p>つながりを整理しています</p>
      <small>あなたのネットワークを安全に読み込んでいます</small>
    </div>
  );
}

function NetworkError({ retry }: { retry(): void }) {
  return (
    <div className="graph-state error-state" role="alert">
      <div className="state-icon">!</div>
      <h2>ネットワークを表示できませんでした</h2>
      <p>接続を確認して、もう一度お試しください。</p>
      <button className="primary-button" onClick={retry} type="button">
        再読み込み
      </button>
    </div>
  );
}

function NetworkEmpty({ retry }: { retry(): void }) {
  return (
    <div className="graph-state empty-state">
      <div className="state-icon">◌</div>
      <h2>表示できるつながりがまだありません</h2>
      <p>データが利用可能になると、ここに人とのつながりが表示されます。</p>
      <button className="secondary-button" onClick={retry} type="button">
        更新する
      </button>
    </div>
  );
}

function RelationshipLegend() {
  return (
    <section
      aria-labelledby="relationship-legend-title"
      className="context-card legend-card"
    >
      <div className="context-card-heading">
        <span>表示の見かた</span>
        <span aria-hidden="true" className="card-heading-line" />
      </div>
      <h2 className="sr-only" id="relationship-legend-title">
        関係性の凡例
      </h2>
      <ul className="legend-list">
        <li>
          <span className="legend-edge legend-edge-strong" />
          <span>
            <b>今も近い</b>
            <small>太さは関係の深さ</small>
          </span>
        </li>
        <li>
          <span className="legend-edge legend-edge-dormant" />
          <span>
            <b>久しぶり</b>
            <small>破線で穏やかに表示</small>
          </span>
        </li>
        <li>
          <span className="legend-edge legend-edge-potential" />
          <span>
            <b>つながる可能性</b>
            <small>2-hop先の人</small>
          </span>
        </li>
      </ul>
    </section>
  );
}

function ClusterContext({ projection }: { projection: GraphProjectionSchema }) {
  return (
    <section
      aria-labelledby="cluster-title"
      className="context-card cluster-card"
    >
      <div className="context-card-heading">
        <span>所属のまとまり</span>
        <span aria-hidden="true" className="card-heading-line" />
      </div>
      <h2 className="sr-only" id="cluster-title">
        所属のまとまり
      </h2>
      <p className="cluster-note">
        色のにじみは所属を示します。境界ではありません。
      </p>
      <ul className="cluster-list">
        {projection.clusters.map((cluster, index) => (
          <li key={cluster.id}>
            <span
              className={`cluster-swatch cluster-swatch-${(index % 6) + 1}`}
            />
            <span>{cluster.label}</span>
            <b>{cluster.memberCount}</b>
          </li>
        ))}
      </ul>
    </section>
  );
}

function CameraControls({
  controller,
}: {
  controller: React.RefObject<NetworkGraphController | null>;
}) {
  return (
    <div aria-label="グラフ表示操作" className="camera-controls" role="group">
      <button
        aria-label="拡大"
        onClick={() => controller.current?.zoomIn()}
        type="button"
      >
        ＋
      </button>
      <button
        aria-label="縮小"
        onClick={() => controller.current?.zoomOut()}
        type="button"
      >
        −
      </button>
      <span />
      <button
        aria-label="全体を表示"
        onClick={() => controller.current?.fit()}
        type="button"
      >
        <Icon>
          <path d="M8 3H3v5m13-5h5v5M8 21H3v-5m13 5h5v-5" />
        </Icon>
      </button>
      <button
        className="center-control"
        onClick={() => controller.current?.centerOnFocal()}
        type="button"
      >
        <Icon>
          <circle cx="12" cy="12" r="6" />
          <circle cx="12" cy="12" fill="currentColor" r="1.5" />
          <path d="M12 2v3m0 14v3M2 12h3m14 0h3" />
        </Icon>
        自分を中心に
      </button>
    </div>
  );
}

function NetworkReady({ projection }: { projection: GraphProjectionSchema }) {
  const [hopMode, setHopMode] = useState<VisibleHopMode>("TWO_HOP");
  const graphController = useRef<NetworkGraphController>(null);
  const model = useMemo(
    () => buildNetworkGraph(projection, hopMode),
    [hopMode, projection],
  );
  const visibleCount = model.graph.order;

  return (
    <>
      <div className="network-toolbar">
        <div
          className="hop-switch"
          role="group"
          aria-label="表示するつながりの範囲"
        >
          <button
            aria-pressed={hopMode === "ONE_HOP"}
            onClick={() => setHopMode("ONE_HOP")}
            type="button"
          >
            1-hop
          </button>
          <button
            aria-pressed={hopMode === "TWO_HOP"}
            onClick={() => setHopMode("TWO_HOP")}
            type="button"
          >
            2-hopまで
          </button>
        </div>
        <div
          aria-label={`${visibleCount}人を表示。全体${projection.meta.totalNetworkSize}人`}
          aria-live="polite"
          className="network-count"
        >
          <span>{visibleCount}</span>人を表示
          <small>全体 {projection.meta.totalNetworkSize}人</small>
        </div>
      </div>
      <div className="network-workspace">
        <section aria-labelledby="network-canvas-title" className="graph-panel">
          <h2 className="sr-only" id="network-canvas-title">
            つながりのグラフ
          </h2>
          <div className="graph-atmosphere" />
          <NetworkGraphCanvas model={model} ref={graphController} />
          <CameraControls controller={graphController} />
          <div className="canvas-hint">
            <span />
            ドラッグで移動 ・ スクロールで拡大縮小
          </div>
        </section>
        <aside aria-label="グラフの補足情報" className="network-context">
          <RelationshipLegend />
          <ClusterContext projection={projection} />
          <div className="privacy-note">
            <Icon>
              <path d="M6 10V8a6 6 0 0 1 12 0v2m-13 0h14v11H5V10Z" />
              <path d="M12 14v3" />
            </Icon>
            <span>
              <b>あなただけのネットワーク</b>
              <small>関係性の表示は他の人には見えません</small>
            </span>
          </div>
        </aside>
      </div>
      <p className="sr-only">
        あなたを含む{visibleCount}人を表示しています。1-hopは
        {projection.meta.oneHopCount}人、2-hopは{projection.meta.twoHopCount}
        人です。
      </p>
    </>
  );
}

export function NetworkScreen() {
  const networkQuery = useQuery({
    queryFn: ({ signal }) => fetchNetworkProjection(signal),
    queryKey: ["current-network"],
  });

  return (
    <div className="app-shell">
      <AppRail />
      <main className="network-page">
        <header className="network-header">
          <div>
            <p className="page-kicker">PERSONAL NETWORK</p>
            <h1>My Network</h1>
            <p>人とのつながりを、思い出しやすい形で。</p>
          </div>
          <div className="header-status">
            <span />
            プライベート表示
          </div>
        </header>
        {networkQuery.isPending ? <NetworkLoading /> : null}
        {networkQuery.isError ? (
          <NetworkError retry={() => void networkQuery.refetch()} />
        ) : null}
        {networkQuery.data && networkQuery.data.nodes.length === 0 ? (
          <NetworkEmpty retry={() => void networkQuery.refetch()} />
        ) : null}
        {networkQuery.data && networkQuery.data.nodes.length > 0 ? (
          <NetworkReady projection={networkQuery.data} />
        ) : null}
      </main>
    </div>
  );
}
