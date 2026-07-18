"use client"

import { useEffect, useRef } from "react"
import * as THREE from "three"

type LearningCoreSceneProps = {
  onUnavailable: () => void
}

const sceneTargets = [
  { scale: 1, pointSize: 0.037, lineOpacity: 0.36, rotation: 0.08 },
  { scale: 0.88, pointSize: 0.047, lineOpacity: 0.5, rotation: 0.28 },
  { scale: 1.14, pointSize: 0.036, lineOpacity: 0.55, rotation: 0.53 },
  { scale: 0.96, pointSize: 0.052, lineOpacity: 0.45, rotation: 0.78 },
  { scale: 0.78, pointSize: 0.042, lineOpacity: 0.3, rotation: 1.02 },
]

export function LearningCoreScene({
  onUnavailable,
}: LearningCoreSceneProps) {
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const host = hostRef.current
    const reducedMotion = typeof window.matchMedia === "function"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches

    if (!host || reducedMotion || typeof window.WebGLRenderingContext === "undefined") {
      onUnavailable()
      return
    }

    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" })
    } catch {
      onUnavailable()
      return
    }

    const mediaQuery = typeof window.matchMedia === "function"
      ? window.matchMedia("(max-width: 720px), (pointer: coarse)")
      : { matches: false }
    const count = mediaQuery.matches ? 650 : 1550
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100)
    const clock = new THREE.Clock()
    const group = new THREE.Group()
    const dragRotation = new THREE.Vector2()
    const dragState = { pointerId: -1, x: 0, y: 0 }
    const material = new THREE.PointsMaterial({
      color: 0x8aa7ff,
      size: 0.04,
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x7898ff,
      transparent: true,
      opacity: 0.36,
      blending: THREE.AdditiveBlending,
    })
    const coreMaterial = new THREE.MeshBasicMaterial({
      color: 0x90a5ff,
      transparent: true,
      opacity: 0.18,
      wireframe: true,
    })

    const positions = new Float32Array(count * 3)
    for (let index = 0; index < count; index += 1) {
      const radius = 1.05 + Math.random() * 1.1
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      positions[index * 3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[index * 3 + 1] = radius * Math.cos(phi)
      positions[index * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta)
    }

    const pointsGeometry = new THREE.BufferGeometry()
    pointsGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3))
    const points = new THREE.Points(pointsGeometry, material)

    const linePoints: number[] = []
    const links = mediaQuery.matches ? 75 : 230
    for (let index = 0; index < links; index += 1) {
      const from = Math.floor(Math.random() * count) * 3
      const to = Math.floor(Math.random() * count) * 3
      linePoints.push(
        positions[from], positions[from + 1], positions[from + 2],
        positions[to], positions[to + 1], positions[to + 2],
      )
    }
    const linesGeometry = new THREE.BufferGeometry()
    linesGeometry.setAttribute("position", new THREE.Float32BufferAttribute(linePoints, 3))
    const lines = new THREE.LineSegments(linesGeometry, lineMaterial)
    const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.72, 2), coreMaterial)
    const orbit = new THREE.Mesh(
      new THREE.TorusGeometry(1.72, 0.006, 6, 120),
      new THREE.MeshBasicMaterial({ color: 0x728aff, transparent: true, opacity: 0.32 }),
    )

    group.add(points, lines, core, orbit)
    scene.add(group)
    camera.position.set(0, 0, 6.25)
    renderer.setClearColor(0x000000, 0)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, mediaQuery.matches ? 1.25 : 1.8))
    host.appendChild(renderer.domElement)

    const resize = () => {
      const { width, height } = host.getBoundingClientRect()
      camera.aspect = Math.max(width / Math.max(height, 1), 0.1)
      camera.updateProjectionMatrix()
      renderer.setSize(width, height, false)
    }
    const onPointerDown = (event: PointerEvent) => {
      if (mediaQuery.matches || event.button !== 0 || event.pointerType !== "mouse") return
      dragState.pointerId = event.pointerId
      dragState.x = event.clientX
      dragState.y = event.clientY
      renderer.domElement.setPointerCapture(event.pointerId)
    }
    const onPointerMove = (event: PointerEvent) => {
      if (event.pointerId !== dragState.pointerId) return
      dragRotation.x += (event.clientX - dragState.x) * 0.006
      dragRotation.y += (event.clientY - dragState.y) * 0.005
      dragState.x = event.clientX
      dragState.y = event.clientY
    }
    const endDrag = (event: PointerEvent) => {
      if (event.pointerId !== dragState.pointerId) return
      if (renderer.domElement.hasPointerCapture(event.pointerId)) renderer.domElement.releasePointerCapture(event.pointerId)
      dragState.pointerId = -1
    }
    const onVisibilityChange = () => {
      clock.running = !document.hidden
    }
    const onContextLost = (event: Event) => {
      event.preventDefault()
      onUnavailable()
    }

    const observer = new ResizeObserver(resize)
    observer.observe(host)
    renderer.domElement.addEventListener("pointerdown", onPointerDown)
    renderer.domElement.addEventListener("pointermove", onPointerMove)
    renderer.domElement.addEventListener("pointerup", endDrag)
    renderer.domElement.addEventListener("pointercancel", endDrag)
    document.addEventListener("visibilitychange", onVisibilityChange)
    renderer.domElement.addEventListener("webglcontextlost", onContextLost)
    resize()

    let frame = 0
    const render = () => {
      frame = window.requestAnimationFrame(render)
      const time = clock.getElapsedTime()
      const target = sceneTargets[0]

      group.scale.setScalar(target.scale)
      group.rotation.y = time * 0.08 + target.rotation + dragRotation.x
      group.rotation.x = Math.sin(time * 0.16) * 0.08 + dragRotation.y
      core.rotation.y = -time * 0.2
      core.rotation.x = time * 0.1
      orbit.rotation.x = 1.24 + Math.sin(time * 0.12) * 0.12
      orbit.rotation.z = time * 0.08
      material.size = target.pointSize
      lineMaterial.opacity = target.lineOpacity
      camera.position.x = 0
      camera.position.y = 0
      camera.lookAt(0, 0, 0)
      renderer.render(scene, camera)
    }
    render()

    return () => {
      window.cancelAnimationFrame(frame)
      observer.disconnect()
      renderer.domElement.removeEventListener("pointerdown", onPointerDown)
      renderer.domElement.removeEventListener("pointermove", onPointerMove)
      renderer.domElement.removeEventListener("pointerup", endDrag)
      renderer.domElement.removeEventListener("pointercancel", endDrag)
      document.removeEventListener("visibilitychange", onVisibilityChange)
      renderer.domElement.removeEventListener("webglcontextlost", onContextLost)
      pointsGeometry.dispose()
      linesGeometry.dispose()
      core.geometry.dispose()
      orbit.geometry.dispose()
      material.dispose()
      lineMaterial.dispose()
      coreMaterial.dispose()
      ;(orbit.material as THREE.Material).dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [onUnavailable])

  return <div ref={hostRef} aria-hidden="true" className="landing-scene-canvas" />
}
