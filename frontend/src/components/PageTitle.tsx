import type { ReactNode } from 'react'

export function PageTitle({ title, description, extra }: { title: string; description: string; extra?: ReactNode }) {
  return (
    <div className="page-title">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {extra ? <div className="page-title-extra">{extra}</div> : null}
    </div>
  )
}
