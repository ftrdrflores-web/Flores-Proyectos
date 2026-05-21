import { useRef, useEffect, useState } from 'react'
import { gsap } from 'gsap'

// SVG del bárbaro dibujado en 2D estilo CoC
const BarbarianSVG = ({ state }) => (
  <svg
    viewBox="0 0 80 100"
    xmlns="http://www.w3.org/2000/svg"
    style={{ width: 64, height: 80, overflow: 'visible' }}
  >
    {/* Casco */}
    <ellipse cx="40" cy="22" rx="16" ry="12" fill="#D4A017" />
    <ellipse cx="40" cy="20" rx="13" ry="9" fill="#E8B820" />
    <rect x="27" y="24" width="26" height="5" rx="2" fill="#C49010" />
    {/* Plumas del casco */}
    <ellipse cx="28" cy="14" rx="4" ry="8" fill="#C8C8C8" transform="rotate(-20 28 14)" />
    <ellipse cx="40" cy="10" rx="4" ry="9" fill="#E0E0E0" />
    <ellipse cx="52" cy="14" rx="4" ry="8" fill="#C8C8C8" transform="rotate(20 52 14)" />
    {/* Cara */}
    <ellipse cx="40" cy="34" rx="13" ry="12" fill="#D4845A" />
    {/* Barba */}
    <ellipse cx="40" cy="43" rx="10" ry="6" fill="#C4A020" />
    {/* Ojos */}
    <ellipse cx="35" cy="31" rx="3" ry="3.5" fill="white" />
    <ellipse cx="45" cy="31" rx="3" ry="3.5" fill="white" />
    <ellipse cx={state === 'idle' ? '35.5' : '36'} cy="31.5" rx="1.8" ry="2" fill="#2244AA" />
    <ellipse cx={state === 'idle' ? '45.5' : '46'} cy="31.5" rx="1.8" ry="2" fill="#2244AA" />
    {/* Cejas */}
    <path d={state === 'thinking' ? 'M32 27 Q35 29 38 27' : 'M32 27 Q35 26 38 28'} stroke="#8B6010" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    <path d={state === 'thinking' ? 'M42 27 Q45 29 48 27' : 'M42 28 Q45 26 48 27'} stroke="#8B6010" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    {/* Boca */}
    {state === 'thinking'
      ? <path d="M36 40 Q40 39 44 40" stroke="#8B5010" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      : state === 'excited'
      ? <path d="M35 40 Q40 45 45 40" stroke="#8B5010" strokeWidth="2" fill="#C06030" strokeLinecap="round" />
      : <path d="M36 40 Q40 42 44 40" stroke="#8B5010" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    }
    {/* Cuerpo */}
    <rect x="28" y="46" width="24" height="22" rx="4" fill="#D4845A" />
    {/* Cinturón */}
    <rect x="26" y="64" width="28" height="6" rx="2" fill="#8B4513" />
    <rect x="37" y="63" width="6" height="8" rx="1" fill="#C0A030" />
    {/* Brazos */}
    <ellipse cx="22" cy="54" rx="6" ry="10" fill="#D4845A" transform="rotate(-10 22 54)" />
    <ellipse cx="58" cy="54" rx="6" ry="10" fill="#D4845A" transform="rotate(10 58 54)" />
    {/* Brazaletes */}
    <rect x="16" y="58" width="12" height="4" rx="2" fill="#8B4513" />
    <rect x="52" y="58" width="12" height="4" rx="2" fill="#8B4513" />
    {/* Espada — solo en excited */}
    {state === 'excited' && (
      <g transform="translate(58 38) rotate(35)">
        <rect x="-2" y="-20" width="4" height="28" rx="1" fill="#C0C0C0" />
        <rect x="-6" y="-2" width="12" height="3" rx="1" fill="#C49010" />
        <rect x="-1.5" y="8" width="3" height="6" rx="1" fill="#8B4513" />
      </g>
    )}
    {/* Mano pensativa */}
    {state === 'thinking' && (
      <ellipse cx="25" cy="44" rx="5" ry="5" fill="#D4845A" />
    )}
    {/* Piernas */}
    <rect x="29" y="70" width="9" height="16" rx="3" fill="#8B2020" />
    <rect x="42" y="70" width="9" height="16" rx="3" fill="#8B2020" />
    {/* Sandalias */}
    <ellipse cx="33" cy="87" rx="7" ry="3" fill="#8B4513" />
    <ellipse cx="47" cy="87" rx="7" ry="3" fill="#8B4513" />
    {/* Puntos de decoración en brazaletes */}
    <circle cx="19" cy="60" r="1" fill="#E8B820" />
    <circle cx="23" cy="60" r="1" fill="#E8B820" />
    <circle cx="55" cy="60" r="1" fill="#E8B820" />
    <circle cx="59" cy="60" r="1" fill="#E8B820" />
    {/* Burbuja de pensamiento */}
    {state === 'thinking' && (
      <g>
        <circle cx="12" cy="28" r="3" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
        <circle cx="7" cy="20" r="4" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
        <circle cx="3" cy="11" r="6" fill="rgba(255,255,255,0.10)" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
        <text x="-4" y="14" fontSize="7" fill="rgba(255,255,255,0.7)">...</text>
      </g>
    )}
  </svg>
)

const Barbarian = () => {
  const containerRef = useRef(null)
  const bodyRef      = useRef(null)
  const [state, setState] = useState('idle')
  const idleTimer = useRef(null)

  // Idle float animation
  useEffect(() => {
    const tl = gsap.timeline({ repeat: -1, yoyo: true })
    tl.to(bodyRef.current, {
      y: -6,
      duration: 1.8,
      ease: 'sine.inOut',
    })
    return () => tl.kill()
  }, [])

  // Idle detection — thinking after 8s no interaction
  useEffect(() => {
    const resetTimer = () => {
      clearTimeout(idleTimer.current)
      if (state === 'thinking') setState('idle')
      idleTimer.current = setTimeout(() => setState('thinking'), 8000)
    }
    window.addEventListener('mousemove', resetTimer)
    window.addEventListener('click',     resetTimer)
    resetTimer()
    return () => {
      window.removeEventListener('mousemove', resetTimer)
      window.removeEventListener('click',     resetTimer)
      clearTimeout(idleTimer.current)
    }
  }, [state])

  // Click reaction
  useEffect(() => {
    const handleClick = () => {
      setState('excited')
      gsap.to(bodyRef.current, {
        scale: 1.15,
        duration: 0.15,
        yoyo: true,
        repeat: 1,
        ease: 'power2.out',
        onComplete: () => setState('idle'),
      })
    }
    window.addEventListener('click', handleClick)
    return () => window.removeEventListener('click', handleClick)
  }, [])

  return (
    <div
      ref={containerRef}
      className="fixed bottom-24 right-6 z-40 cursor-pointer select-none"
      title="¡Soy el Bárbaro!"
      onClick={() => {
        setState('excited')
        gsap.to(bodyRef.current, {
          rotation: [-8, 8, -5, 5, 0],
          duration: 0.5,
          ease: 'power1.inOut',
          onComplete: () => setState('idle'),
        })
      }}
    >
      <div ref={bodyRef} style={{ filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.4))' }}>
        <BarbarianSVG state={state} />
      </div>
    </div>
  )
}

export default Barbarian
