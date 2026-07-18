"use client"

import { BrainCircuit, Menu, MoveRight, X } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"

import { UserIdLoginForm } from "@/components/auth/user-id-login-form"
import { landingChapters } from "@/components/landing/landing-content"
import { LearningCoreScene } from "@/components/landing/learning-core-scene"
import { SceneFallback } from "@/components/landing/scene-fallback"

export function ImmersiveLoginPage() {
  const [activeChapter, setActiveChapter] = useState(0)
  const [isLoginOpen, setIsLoginOpen] = useState(false)
  const [isSceneUnavailable, setIsSceneUnavailable] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const activeChapterRef = useRef(activeChapter)
  const navigationLockedRef = useRef(false)
  const navigationTimerRef = useRef<number | null>(null)
  const touchStartYRef = useRef<number | null>(null)
  const handleSceneUnavailable = useCallback(() => setIsSceneUnavailable(true), [])

  useEffect(() => {
    activeChapterRef.current = activeChapter
  }, [activeChapter])

  const goToChapter = useCallback((requestedIndex: number) => {
    if (navigationLockedRef.current) return

    const index = Math.min(Math.max(requestedIndex, 0), landingChapters.length - 1)
    if (index === activeChapterRef.current) return
    const section = document.getElementById(landingChapters[index].id)
    if (!section) return

    navigationLockedRef.current = true
    setActiveChapter(index)
    window.scrollTo({ top: section.offsetTop, behavior: "smooth" })
    if (navigationTimerRef.current) window.clearTimeout(navigationTimerRef.current)
    navigationTimerRef.current = window.setTimeout(() => {
      navigationLockedRef.current = false
      navigationTimerRef.current = null
    }, 700)
  }, [])

  useEffect(() => {
    const isInteractiveTarget = (target: EventTarget | null) => {
      const element = target instanceof HTMLElement ? target : null
      return Boolean(element?.closest("input, textarea, select, button, a, [contenteditable=true]"))
    }
    const onWheel = (event: WheelEvent) => {
      if (isLoginOpen || isInteractiveTarget(event.target) || event.deltaY === 0) return
      event.preventDefault()
      goToChapter(activeChapterRef.current + (event.deltaY > 0 ? 1 : -1))
    }
    const onTouchStart = (event: TouchEvent) => {
      touchStartYRef.current = event.touches[0]?.clientY ?? null
    }
    const onTouchMove = (event: TouchEvent) => {
      if (!isLoginOpen && touchStartYRef.current !== null) event.preventDefault()
    }
    const onTouchEnd = (event: TouchEvent) => {
      const startY = touchStartYRef.current
      const endY = event.changedTouches[0]?.clientY
      touchStartYRef.current = null
      if (isLoginOpen || startY === null || endY === undefined) return
      const distance = startY - endY
      if (Math.abs(distance) >= 36) goToChapter(activeChapterRef.current + (distance > 0 ? 1 : -1))
    }
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsLoginOpen(false)
        setIsMenuOpen(false)
        return
      }
      if (isLoginOpen || isInteractiveTarget(event.target)) return
      const direction = event.key === "ArrowDown" || event.key === "PageDown" ? 1 : event.key === "ArrowUp" || event.key === "PageUp" ? -1 : 0
      if (direction !== 0) {
        event.preventDefault()
        goToChapter(activeChapterRef.current + direction)
      }
    }

    window.addEventListener("wheel", onWheel, { passive: false })
    window.addEventListener("touchstart", onTouchStart, { passive: true })
    window.addEventListener("touchmove", onTouchMove, { passive: false })
    window.addEventListener("touchend", onTouchEnd, { passive: true })
    window.addEventListener("keydown", onKeyDown)
    return () => {
      window.removeEventListener("wheel", onWheel)
      window.removeEventListener("touchstart", onTouchStart)
      window.removeEventListener("touchmove", onTouchMove)
      window.removeEventListener("touchend", onTouchEnd)
      window.removeEventListener("keydown", onKeyDown)
      if (navigationTimerRef.current) window.clearTimeout(navigationTimerRef.current)
    }
  }, [goToChapter, isLoginOpen])

  const openLogin = () => {
    setIsMenuOpen(false)
    setIsLoginOpen(true)
  }

  return (
    <main className="landing-page">
      <div className="landing-page__backdrop">
        <SceneFallback />
        {!isSceneUnavailable ? (
          <LearningCoreScene
            onUnavailable={handleSceneUnavailable}
          />
        ) : null}
      </div>

      <header className="landing-nav">
        <a className="landing-brand" href="#intro" aria-label="智学引擎首页">
          <span className="landing-brand__mark"><BrainCircuit aria-hidden="true" /></span>
          <span>智学引擎</span>
        </a>
        <nav className={isMenuOpen ? "landing-nav__links landing-nav__links--open" : "landing-nav__links"} aria-label="页面章节">
          {landingChapters.slice(1).map((chapter, index) => (
            <a
              key={chapter.id}
              className={activeChapter === index + 1 ? "landing-nav__link landing-nav__link--active" : "landing-nav__link"}
              href={`#${chapter.id}`}
              onClick={(event) => {
                event.preventDefault()
                setIsMenuOpen(false)
                goToChapter(index + 1)
              }}
            >
              {chapter.title}
            </a>
          ))}
        </nav>
        <div className="landing-nav__actions">
          <button className="landing-login-trigger" type="button" onClick={openLogin}>
            进入学习空间 <MoveRight aria-hidden="true" />
          </button>
          <button
            className="landing-menu-trigger"
            type="button"
            aria-label={isMenuOpen ? "关闭导航" : "打开导航"}
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen((current) => !current)}
          >
            {isMenuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
          </button>
        </div>
      </header>

      <div className="landing-progress" aria-hidden="true">
        {landingChapters.map((chapter, index) => <span key={chapter.id} className={activeChapter === index ? "landing-progress__dot landing-progress__dot--active" : "landing-progress__dot"} />)}
      </div>

      <div className="landing-chapters">
        {landingChapters.map((chapter, index) => (
          <section key={chapter.id} id={chapter.id} className={index === 0 ? "landing-chapter landing-chapter--intro" : "landing-chapter"} aria-labelledby={`${chapter.id}-title`}>
            <div className={activeChapter === index ? "landing-chapter__content landing-chapter__content--active" : "landing-chapter__content"}>
              <p className="landing-chapter__eyebrow">{chapter.index} / {chapter.eyebrow}</p>
              <h1 id={`${chapter.id}-title`}>{chapter.title}</h1>
              <p className="landing-chapter__statement">{chapter.description}</p>
              <p className="landing-chapter__detail">{chapter.detail}</p>
              {index === 0 ? (
                <button className="landing-primary-action" type="button" onClick={openLogin}>
                  开启学习空间 <MoveRight aria-hidden="true" />
                </button>
              ) : null}
            </div>
            <p className="landing-chapter__index" aria-hidden="true">{chapter.index}</p>
          </section>
        ))}
      </div>

      {isLoginOpen ? (
        <div className="landing-login-overlay" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setIsLoginOpen(false) }}>
          <section className="landing-login-dialog" role="dialog" aria-modal="true" aria-label="进入学习空间">
            <button className="landing-login-dialog__close" type="button" aria-label="关闭登录窗口" onClick={() => setIsLoginOpen(false)}><X aria-hidden="true" /></button>
            <p className="landing-login-dialog__eyebrow">ZHIXUE ENGINE / ACCESS</p>
            <h2>进入学习空间</h2>
            <p>使用你的用户 ID，继续连接学习画像与成长记录。</p>
            <UserIdLoginForm />
          </section>
        </div>
      ) : null}
    </main>
  )
}
