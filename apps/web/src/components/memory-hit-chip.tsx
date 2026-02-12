export function MemoryHitChip(props: { memoryId: string }) {
  return (
    <span className="memory-chip" data-testid="memory-hit-chip">
      hit:{props.memoryId}
    </span>
  )
}
