// stale: rows are the last known data from a backend that no longer answers.
export default function DataPanel({ id, title, badge, columns, isEmpty, emptyTitle, emptyBody, stale, children }) {
  return (
    <section aria-labelledby={id} className="flex min-h-96 min-w-0 flex-col border border-rule">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-rule bg-asphalt-raised px-4 py-3">
        <h2 id={id} className="font-sign text-lg leading-none font-bold tracking-[0.08em] uppercase">
          {title}
        </h2>
        {badge}
      </header>

      <div className="max-h-[36rem] overflow-auto">
        <table className="w-full border-collapse text-left text-sm sm:min-w-120">
          <thead className="sticky top-0 bg-asphalt">
            <tr className="border-b border-rule-soft">
              {columns.map((c) => (
                <th
                  key={c}
                  scope="col"
                  className="px-3 py-2.5 text-xs font-semibold tracking-[0.1em] whitespace-nowrap text-muted uppercase sm:px-4"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={`transition-opacity duration-200 ease-sign ${stale ? 'opacity-45' : ''}`}>{children}</tbody>
        </table>
      </div>

      {isEmpty && (
        <div className="grid flex-1 place-items-center px-6 py-16 text-center">
          <div>
            <p className="font-sign text-lg font-bold tracking-[0.06em] uppercase">{emptyTitle}</p>
            <p className="mx-auto mt-1 max-w-[42ch] text-muted">{emptyBody}</p>
          </div>
        </div>
      )}
    </section>
  )
}

// Shared cell styling so both panels keep the same rhythm.
export const cell = 'px-3 py-2.5 align-top sm:px-4'
