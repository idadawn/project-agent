"use client"

import React from "react"

type FileItem = { name: string; path: string }

function dedupeByPath(files: FileItem[]) {
  const seen = new Set<string>()
  return files.filter((f) => (seen.has(f.path) ? false : (seen.add(f.path), true)))
}

export default function DocumentList({
  files,
  onOpen,
}: {
  files: FileItem[]
  onOpen?: (f: FileItem) => void
}) {
  const list = dedupeByPath(files)
  return (
    <ul className="space-y-1">
      {list.map((f, idx) => (
        <li
          key={f.path}
          className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-gray-50 cursor-pointer"
          onClick={() => onOpen?.(f)}
        >
          <span className="w-6 text-right tabular-nums">{idx + 1}.</span>
          <span className="truncate">{f.name}</span>
        </li>
      ))}
    </ul>
  )
}


