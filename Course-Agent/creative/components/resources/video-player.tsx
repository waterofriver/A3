export function VideoPlayer({
  poster,
  src,
}: {
  poster?: string | null
  src: string
}) {
  return (
    <video
      className="aspect-video w-full bg-black object-contain"
      controls
      data-testid="video-player"
      poster={poster || undefined}
      preload="metadata"
      src={src}
    />
  )
}
