import html
from pathlib import Path
from typing import Dict


def write_html_report(result: Dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "report.html"
    path.write_text(render_html_report(result), encoding="utf-8")
    return path


def render_html_report(result: Dict) -> str:
    summary = result.get("summary", {})
    video = result.get("video", {})
    episodes = result.get("episodes", [])
    status = "Нарушения обнаружены" if summary.get("violations_found") else "Нарушения не обнаружены"
    status_class = "bad" if summary.get("violations_found") else "good"

    episode_rows = []
    for index, episode in enumerate(episodes, start=1):
        evidence = "".join(
            '<a href="{src}"><img src="{src}" alt="Кадр {idx}"></a>'.format(
                src=html.escape(path),
                idx=index,
            )
            for path in episode.get("evidence_paths", [])
        )
        episode_rows.append(
            """
            <section class="episode">
              <h3>Эпизод {index}</h3>
              <dl>
                <dt>Начало</dt><dd>{start}</dd>
                <dt>Окончание</dt><dd>{end}</dd>
                <dt>Кадров с нарушением</dt><dd>{hits}</dd>
                <dt>Макс. уверенность</dt><dd>{confidence:.2f}</dd>
                <dt>Причины</dt><dd>{reasons}</dd>
              </dl>
              <div class="evidence">{evidence}</div>
            </section>
            """.format(
                index=index,
                start=_format_time(episode.get("start_time", 0.0)),
                end=_format_time(episode.get("end_time", 0.0)),
                hits=episode.get("hit_count", 0),
                confidence=float(episode.get("max_confidence", 0.0)),
                reasons=html.escape(", ".join(episode.get("reasons", []))),
                evidence=evidence or "<p>Кадры не сохранены.</p>",
            )
        )

    if not episode_rows:
        episode_rows.append("<p>Подтвержденных эпизодов отсутствия каски нет.</p>")

    return """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Отчет анализа касок</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    .status {{ padding: 12px 16px; border-radius: 8px; font-weight: bold; }}
    .good {{ background: #e7f7ed; color: #0b6b2b; }}
    .bad {{ background: #fde8e8; color: #9b1c1c; }}
    dl {{ display: grid; grid-template-columns: 220px 1fr; gap: 6px 16px; }}
    dt {{ font-weight: bold; }}
    .episode {{ border: 1px solid #d8dee4; border-radius: 8px; padding: 16px; margin-top: 16px; }}
    .evidence img {{ max-width: 280px; margin: 8px 12px 8px 0; border: 1px solid #d8dee4; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Отчет анализа наличия касок</h1>
  <p class="status {status_class}">{status}</p>

  <h2>Видео</h2>
  <dl>
    <dt>Файл</dt><dd>{video_name}</dd>
    <dt>Исходный FPS</dt><dd>{source_fps}</dd>
    <dt>Всего кадров</dt><dd>{frame_count}</dd>
    <dt>Обработано кадров</dt><dd>{processed_frames}</dd>
    <dt>Кадров с признаками нарушения</dt><dd>{violation_frames}</dd>
    <dt>Подтвержденных эпизодов</dt><dd>{episode_count}</dd>
  </dl>

  <h2>Эпизоды</h2>
  {episodes}

  <p>Машинно-читаемый отчет: <code>analysis.json</code></p>
</body>
</html>
""".format(
        status_class=status_class,
        status=status,
        video_name=html.escape(video.get("name", "")),
        source_fps=video.get("source_fps", 0),
        frame_count=video.get("frame_count", 0),
        processed_frames=summary.get("processed_frames", 0),
        violation_frames=summary.get("frames_with_violations", 0),
        episode_count=summary.get("episode_count", 0),
        episodes="\n".join(episode_rows),
    )


def _format_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    remaining = seconds - minutes * 60
    hours = minutes // 60
    minutes = minutes % 60
    return "%02d:%02d:%05.2f" % (hours, minutes, remaining)
