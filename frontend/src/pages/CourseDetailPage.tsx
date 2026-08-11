/**
 * Course Detail Page
 * Before Enroll: Shows course overview, module structure & locked preview teaser
 * After Enroll: Unlocks interactive module video player, lesson progress checklist & source code
 */

import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Navbar } from '../components/layout/Navbar'
import { getProducts, Product } from '../api/products'
import { trackEvent, getMyEvents } from '../api/events'
import { refreshRecommendations } from '../api/recommendations'
import { useAuthStore } from '../store/authStore'
import { 
  HiCheckCircle, 
  HiClock, 
  HiAcademicCap, 
  HiArrowLeft, 
  HiSparkles,
  HiBookmark,
  HiBadgeCheck,
  HiLockClosed,
  HiCode,
  HiDocumentText
} from 'react-icons/hi'

import { FaYoutube } from 'react-icons/fa'

const getYouTubeVideoInfo = (category: string, moduleIdx: number = 0, title: string = '') => {
  const textToMatch = `${category || ''} ${title || ''}`.toLowerCase()
  
  const videoMap: Record<string, { embed: string; watch: string; channel: string }[]> = {
    tailwind_css: [
      { 
        embed: 'https://www.youtube.com/embed/ft30zcMlFao', 
        watch: 'https://www.youtube.com/watch?v=ft30zcMlFao',
        channel: 'freeCodeCamp (Module 1: Tailwind CSS Full Course for Beginners)'
      },
      { 
        embed: 'https://www.youtube.com/embed/lCxcTsOHrjo', 
        watch: 'https://www.youtube.com/watch?v=lCxcTsOHrjo',
        channel: 'Traversy Media (Module 2: CSS Grid & Flexbox Masterclass)'
      },
      { 
        embed: 'https://www.youtube.com/embed/dFgzHOX84xQ', 
        watch: 'https://www.youtube.com/watch?v=dFgzHOX84xQ',
        channel: 'freeCodeCamp (Module 3: Advanced CSS Animations & Dark Mode)'
      },
      { 
        embed: 'https://www.youtube.com/embed/mr15Xzb1Ook', 
        watch: 'https://www.youtube.com/watch?v=mr15Xzb1Ook',
        channel: 'Traversy Media (Module 4: Tailwind CSS Project Build)'
      }
    ],
    ios_swift: [
      { 
        embed: 'https://www.youtube.com/embed/Ulp1Kimblg0', 
        watch: 'https://www.youtube.com/watch?v=Ulp1Kimblg0',
        channel: 'freeCodeCamp (Module 1: Swift Basics & Language Syntax)'
      },
      { 
        embed: 'https://www.youtube.com/embed/F2ojC6TNwws', 
        watch: 'https://www.youtube.com/watch?v=F2ojC6TNwws',
        channel: 'Sean Allen (Module 2: SwiftUI Interface Design)'
      },
      { 
        embed: 'https://www.youtube.com/embed/Ulp1Kimblg0', 
        watch: 'https://www.youtube.com/watch?v=Ulp1Kimblg0',
        channel: 'freeCodeCamp (Module 3: CoreData & Local Persistence)'
      },
      { 
        embed: 'https://www.youtube.com/embed/F2ojC6TNwws', 
        watch: 'https://www.youtube.com/watch?v=F2ojC6TNwws',
        channel: 'freeCodeCamp (Module 4: App Store Signing & Release)'
      }
    ],
    flutter: [
      { 
        embed: 'https://www.youtube.com/embed/x0uinJvhNxI', 
        watch: 'https://www.youtube.com/watch?v=x0uinJvhNxI',
        channel: 'freeCodeCamp (Module 1: Dart Language Essentials)'
      },
      { 
        embed: 'https://www.youtube.com/embed/VPvVD8t02U8', 
        watch: 'https://www.youtube.com/watch?v=VPvVD8t02U8',
        channel: 'freeCodeCamp (Module 2: Flutter Widgets & Layouts)'
      },
      { 
        embed: 'https://www.youtube.com/embed/d_m5csmrf7I', 
        watch: 'https://www.youtube.com/watch?v=d_m5csmrf7I',
        channel: 'Reso Coder (Module 3: State Management & Provider)'
      },
      { 
        embed: 'https://www.youtube.com/embed/1gDhl4leEzA', 
        watch: 'https://www.youtube.com/watch?v=1gDhl4leEzA',
        channel: 'freeCodeCamp (Module 4: Firebase Integration & App Publishing)'
      }
    ],
    react_native: [
      { 
        embed: 'https://www.youtube.com/embed/0-S5a0eXPoc', 
        watch: 'https://www.youtube.com/watch?v=0-S5a0eXPoc',
        channel: 'freeCodeCamp (Module 1: React Native & Expo Fundamentals)'
      },
      { 
        embed: 'https://www.youtube.com/embed/obH0Po_RdWk', 
        watch: 'https://www.youtube.com/watch?v=obH0Po_RdWk',
        channel: 'freeCodeCamp (Module 2: Native Component Styling & Expo Router)'
      },
      { 
        embed: 'https://www.youtube.com/embed/mJ3bGvy0WAY', 
        watch: 'https://www.youtube.com/watch?v=mJ3bGvy0WAY',
        channel: 'JavaScript Mastery (Module 3: React Navigation & Context API)'
      },
      { 
        embed: 'https://www.youtube.com/embed/0-S5a0eXPoc', 
        watch: 'https://www.youtube.com/watch?v=0-S5a0eXPoc',
        channel: 'freeCodeCamp (Module 4: App Store & Play Store Deployment)'
      }
    ],
    android_kotlin: [
      { 
        embed: 'https://www.youtube.com/embed/F9UC9DY-vIU', 
        watch: 'https://www.youtube.com/watch?v=F9UC9DY-vIU',
        channel: 'freeCodeCamp (Module 1: Kotlin Syntax & Null Safety)'
      },
      { 
        embed: 'https://www.youtube.com/embed/fis26HvvDII', 
        watch: 'https://www.youtube.com/watch?v=fis26HvvDII',
        channel: 'freeCodeCamp (Module 2: Jetpack Compose Declarative UI)'
      },
      { 
        embed: 'https://www.youtube.com/embed/F9UC9DY-vIU', 
        watch: 'https://www.youtube.com/watch?v=F9UC9DY-vIU',
        channel: 'Philipp Lackner (Module 3: Room Database & Offline Storage)'
      },
      { 
        embed: 'https://www.youtube.com/embed/fis26HvvDII', 
        watch: 'https://www.youtube.com/watch?v=fis26HvvDII',
        channel: 'freeCodeCamp (Module 4: Retrofit REST API & MVVM Clean Architecture)'
      }
    ],
    system_design: [
      { 
        embed: 'https://www.youtube.com/embed/m8Icp_Cid5o', 
        watch: 'https://www.youtube.com/watch?v=m8Icp_Cid5o',
        channel: 'freeCodeCamp (Module 1: System Design Fundamentals & CAP Theorem)'
      },
      { 
        embed: 'https://www.youtube.com/embed/UzLMhqg3_Wc', 
        watch: 'https://www.youtube.com/watch?v=UzLMhqg3_Wc',
        channel: 'ByteByteGo (Module 2: Microservices Architecture & API Gateways)'
      },
      { 
        embed: 'https://www.youtube.com/embed/SqcXvc3ZmRU', 
        watch: 'https://www.youtube.com/watch?v=SqcXvc3ZmRU',
        channel: 'freeCodeCamp (Module 3: Database Sharding & Load Balancing)'
      },
      { 
        embed: 'https://www.youtube.com/embed/m8Icp_Cid5o', 
        watch: 'https://www.youtube.com/watch?v=m8Icp_Cid5o',
        channel: 'freeCodeCamp (Module 4: Distributed Caching & Kafka Streams)'
      }
    ],
    data: [
      { 
        embed: 'https://www.youtube.com/embed/qWru-b6m030', 
        watch: 'https://www.youtube.com/watch?v=qWru-b6m030',
        channel: 'freeCodeCamp (Module 1: Data Pipeline Architecture)'
      },
      { 
        embed: 'https://www.youtube.com/embed/K9AnJ9_ZAXE', 
        watch: 'https://www.youtube.com/watch?v=K9AnJ9_ZAXE',
        channel: 'freeCodeCamp (Module 2: PySpark Big Data Processing)'
      },
      { 
        embed: 'https://www.youtube.com/embed/qWru-b6m030', 
        watch: 'https://www.youtube.com/watch?v=qWru-b6m030',
        channel: 'freeCodeCamp (Module 3: Apache Kafka Event Streaming)'
      },
      { 
        embed: 'https://www.youtube.com/embed/K9AnJ9_ZAXE', 
        watch: 'https://www.youtube.com/watch?v=K9AnJ9_ZAXE',
        channel: 'freeCodeCamp (Module 4: Apache Airflow Workflow Orchestration)'
      }
    ],
    database: [
      { 
        embed: 'https://www.youtube.com/embed/HXV3zeQKqGY', 
        watch: 'https://www.youtube.com/watch?v=HXV3zeQKqGY',
        channel: 'freeCodeCamp (Module 1: Relational SQL Fundamentals)'
      },
      { 
        embed: 'https://www.youtube.com/embed/qw--VYLpxG4', 
        watch: 'https://www.youtube.com/watch?v=qw--VYLpxG4',
        channel: 'freeCodeCamp (Module 2: PostgreSQL Indexing & Query Tuning)'
      },
      { 
        embed: 'https://www.youtube.com/embed/c2M-rlkkT5o', 
        watch: 'https://www.youtube.com/watch?v=c2M-rlkkT5o',
        channel: 'freeCodeCamp (Module 3: MongoDB Document Store)'
      },
      { 
        embed: 'https://www.youtube.com/embed/jgpVdJB2sKQ', 
        watch: 'https://www.youtube.com/watch?v=jgpVdJB2sKQ',
        channel: 'freeCodeCamp (Module 4: Redis In-Memory Caching Architecture)'
      }
    ],
    game: [
      { 
        embed: 'https://www.youtube.com/embed/gB1F9G0JXOo', 
        watch: 'https://www.youtube.com/watch?v=gB1F9G0JXOo',
        channel: 'freeCodeCamp (Module 1: C# Math & Game Engine Scripting)'
      },
      { 
        embed: 'https://www.youtube.com/embed/XtQMytORBmM', 
        watch: 'https://www.youtube.com/watch?v=XtQMytORBmM',
        channel: 'freeCodeCamp (Module 2: 2D/3D Physics & Character Mechanics)'
      },
      { 
        embed: 'https://www.youtube.com/embed/gB1F9G0JXOo', 
        watch: 'https://www.youtube.com/watch?v=gB1F9G0JXOo',
        channel: 'freeCodeCamp (Module 3: Unreal Engine 5 Environment & Lighting)'
      },
      { 
        embed: 'https://www.youtube.com/embed/XtQMytORBmM', 
        watch: 'https://www.youtube.com/watch?v=XtQMytORBmM',
        channel: 'freeCodeCamp (Module 4: Multiplayer Networking & Optimization)'
      }
    ],
    design: [
      { 
        embed: 'https://www.youtube.com/embed/FTFaQWZBqQ8', 
        watch: 'https://www.youtube.com/watch?v=FTFaQWZBqQ8',
        channel: 'freeCodeCamp (Module 1: UX Research, Wireframing & Journeys)'
      },
      { 
        embed: 'https://www.youtube.com/embed/c9Wg6Cb_YlU', 
        watch: 'https://www.youtube.com/watch?v=c9Wg6Cb_YlU',
        channel: 'freeCodeCamp (Module 2: Figma Auto-Layout Component Systems)'
      },
      { 
        embed: 'https://www.youtube.com/embed/jwCmIBJ8Jtc', 
        watch: 'https://www.youtube.com/watch?v=jwCmIBJ8Jtc',
        channel: 'freeCodeCamp (Module 3: Interactive Prototyping & Motion)'
      },
      { 
        embed: 'https://www.youtube.com/embed/c9Wg6Cb_YlU', 
        watch: 'https://www.youtube.com/watch?v=c9Wg6Cb_YlU',
        channel: 'freeCodeCamp (Module 4: Design Systems & Hand-off)'
      }
    ],
    cyber: [
      { 
        embed: 'https://www.youtube.com/embed/3Kq1MIfTWCE', 
        watch: 'https://www.youtube.com/watch?v=3Kq1MIfTWCE',
        channel: 'NetworkChuck (Module 1: Wireshark Packet Inspection)'
      },
      { 
        embed: 'https://www.youtube.com/embed/qwA6MmbeGNo', 
        watch: 'https://www.youtube.com/watch?v=qwA6MmbeGNo',
        channel: 'freeCodeCamp (Module 2: Ethical Hacking & Metasploit)'
      },
      { 
        embed: 'https://www.youtube.com/embed/lZAoFs75_cs', 
        watch: 'https://www.youtube.com/watch?v=lZAoFs75_cs',
        channel: 'freeCodeCamp (Module 3: Ghidra Reverse Engineering)'
      },
      { 
        embed: 'https://www.youtube.com/embed/3Kq1MIfTWCE', 
        watch: 'https://www.youtube.com/watch?v=3Kq1MIfTWCE',
        channel: 'freeCodeCamp (Module 4: OWASP Web Security & Audit)'
      }
    ],
    ai: [
      { 
        embed: 'https://www.youtube.com/embed/aircAruvnKk', 
        watch: 'https://www.youtube.com/watch?v=aircAruvnKk',
        channel: '3Blue1Brown (Module 1: Neural Networks Foundations)'
      },
      { 
        embed: 'https://www.youtube.com/embed/V_xro1bcAuA', 
        watch: 'https://www.youtube.com/watch?v=V_xro1bcAuA',
        channel: 'freeCodeCamp (Module 2: PyTorch Deep Learning)'
      },
      { 
        embed: 'https://www.youtube.com/embed/kCc8FmEb1nY', 
        watch: 'https://www.youtube.com/watch?v=kCc8FmEb1nY',
        channel: 'Andrej Karpathy (Module 3: Transformers & LLMs from Scratch)'
      },
      { 
        embed: 'https://www.youtube.com/embed/zjkBMFhNj_g', 
        watch: 'https://www.youtube.com/watch?v=zjkBMFhNj_g',
        channel: 'Andrej Karpathy (Module 4: Intro to Large Language Models)'
      }
    ],
    web: [
      { 
        embed: 'https://www.youtube.com/embed/zJSY8tbf_ys', 
        watch: 'https://www.youtube.com/watch?v=zJSY8tbf_ys',
        channel: 'freeCodeCamp (Module 1: HTML, CSS & JavaScript Foundations)'
      },
      { 
        embed: 'https://www.youtube.com/embed/bMknfKXIFA8', 
        watch: 'https://www.youtube.com/watch?v=bMknfKXIFA8',
        channel: 'freeCodeCamp (Module 2: React 18 & Component Hooks)'
      },
      { 
        embed: 'https://www.youtube.com/embed/Oe421EPjeBE', 
        watch: 'https://www.youtube.com/watch?v=Oe421EPjeBE',
        channel: 'freeCodeCamp (Module 3: Next.js 14 App Router & Server Actions)'
      },
      { 
        embed: 'https://www.youtube.com/embed/zJSY8tbf_ys', 
        watch: 'https://www.youtube.com/watch?v=zJSY8tbf_ys',
        channel: 'freeCodeCamp (Module 4: Node.js Backend Microservices)'
      }
    ],
    blockchain: [
      { 
        embed: 'https://www.youtube.com/embed/M576WGiDBdQ', 
        watch: 'https://www.youtube.com/watch?v=M576WGiDBdQ',
        channel: 'freeCodeCamp (Module 1: Cryptography & Smart Contracts)'
      },
      { 
        embed: 'https://www.youtube.com/embed/M576WGiDBdQ', 
        watch: 'https://www.youtube.com/watch?v=M576WGiDBdQ',
        channel: 'freeCodeCamp (Module 2: Solidity & Ethereum Web3)'
      },
      { 
        embed: 'https://www.youtube.com/embed/M576WGiDBdQ', 
        watch: 'https://www.youtube.com/watch?v=M576WGiDBdQ',
        channel: 'freeCodeCamp (Module 3: DeFi Protocol Architecture)'
      },
      { 
        embed: 'https://www.youtube.com/embed/M576WGiDBdQ', 
        watch: 'https://www.youtube.com/watch?v=M576WGiDBdQ',
        channel: 'freeCodeCamp (Module 4: Rust & Solana Smart Contracts)'
      }
    ],
    cloud: [
      { 
        embed: 'https://www.youtube.com/embed/SOTamWNgDKc', 
        watch: 'https://www.youtube.com/watch?v=SOTamWNgDKc',
        channel: 'freeCodeCamp (Module 1: AWS Solutions Architect)'
      },
      { 
        embed: 'https://www.youtube.com/embed/7XDeI5fyj3w', 
        watch: 'https://www.youtube.com/watch?v=7XDeI5fyj3w',
        channel: 'freeCodeCamp (Module 2: Docker Containers & CI/CD)'
      },
      { 
        embed: 'https://www.youtube.com/embed/X48VuDVv0do', 
        watch: 'https://www.youtube.com/watch?v=X48VuDVv0do',
        channel: 'TechWorld with Nana (Module 3: Kubernetes Orchestration)'
      },
      { 
        embed: 'https://www.youtube.com/embed/m8Icp_Cid5o', 
        watch: 'https://www.youtube.com/watch?v=m8Icp_Cid5o',
        channel: 'freeCodeCamp (Module 4: System Design & Terraform)'
      }
    ]
  }

  let catKey = 'web'
  if (textToMatch.includes('tailwind') || textToMatch.includes('css') || textToMatch.includes('flexbox') || textToMatch.includes('grid')) catKey = 'tailwind_css'
  else if (textToMatch.includes('swift') || textToMatch.includes('swiftui') || (textToMatch.includes('ios') && !textToMatch.includes('react native'))) catKey = 'ios_swift'
  else if (textToMatch.includes('flutter') || textToMatch.includes('dart')) catKey = 'flutter'
  else if (textToMatch.includes('react native') || textToMatch.includes('expo')) catKey = 'react_native'
  else if (textToMatch.includes('kotlin') || textToMatch.includes('android')) catKey = 'android_kotlin'
  else if (textToMatch.includes('system design') || textToMatch.includes('distributed systems') || textToMatch.includes('microservices')) catKey = 'system_design'
  else if (textToMatch.includes('data engineering') || textToMatch.includes('spark') || textToMatch.includes('kafka') || textToMatch.includes('airflow') || textToMatch.includes('etl')) catKey = 'data'
  else if (textToMatch.includes('database') || textToMatch.includes('sql') || textToMatch.includes('postgres') || textToMatch.includes('mongo') || textToMatch.includes('redis')) catKey = 'database'
  else if (textToMatch.includes('game') || textToMatch.includes('unity') || textToMatch.includes('unreal') || textToMatch.includes('c++')) catKey = 'game'
  else if (textToMatch.includes('figma') || textToMatch.includes('ui/ux') || textToMatch.includes('user experience') || textToMatch.includes('wireframe')) catKey = 'design'
  else if (textToMatch.includes('cloud') || textToMatch.includes('devops') || textToMatch.includes('aws') || textToMatch.includes('docker') || textToMatch.includes('kubernetes') || textToMatch.includes('terraform')) catKey = 'cloud'
  else if (/\bai\b/.test(textToMatch) || textToMatch.includes('machine learning') || textToMatch.includes('deep learning') || textToMatch.includes('neural') || textToMatch.includes('pytorch') || textToMatch.includes('tensorflow') || textToMatch.includes('nlp')) catKey = 'ai'
  else if (textToMatch.includes('cyber') || textToMatch.includes('security') || textToMatch.includes('ethical') || textToMatch.includes('hacking')) catKey = 'cyber'
  else if (textToMatch.includes('blockchain') || textToMatch.includes('solidity') || textToMatch.includes('web3') || textToMatch.includes('crypto')) catKey = 'blockchain'

  const list = videoMap[catKey] || videoMap['web']
  return list[moduleIdx % list.length]
}

const getCategoryModules = (category: string, title: string = '') => {
  const textToMatch = `${category || ''} ${title || ''}`.toLowerCase()

  // 1. Tailwind & CSS Layouts
  if (textToMatch.includes('tailwind') || textToMatch.includes('css') || textToMatch.includes('flexbox') || textToMatch.includes('grid')) {
    return [
      {
        module: 'Module 1',
        title: 'Modern CSS Grid, Flexbox & Responsive Layouts',
        lessons: ['CSS Grid vs Flexbox Mechanics', 'Container Queries & Responsive Breakpoints', 'CSS Custom Properties & Fluid Scaling', 'Modern Box Model & Layout Architecture'],
        duration: '3h 15m'
      },
      {
        module: 'Module 2',
        title: 'Tailwind CSS v3 Utility Design Systems',
        lessons: ['Utility-First Architecture', 'Configuring tailwind.config.js Tokens', 'Custom Colors, Spacing & Breakpoints', '@apply Directive & Component Abstractions'],
        duration: '4h 00m'
      },
      {
        module: 'Module 3',
        title: 'Advanced CSS Animations & Dark Mode',
        lessons: ['CSS Transitions & Keyframe Animations', 'Tailwind Dark Mode Integration', 'Glassmorphism & Backdrop Filters', 'Micro-Interactions & Hover Effects'],
        duration: '3h 45m'
      },
      {
        module: 'Module 4',
        title: 'Production CSS Optimization & Component Library',
        lessons: ['Purging Unused CSS with PostCSS', 'Building Reusable Design Primitives', 'Cross-Browser Compatibility & Autoprefixer', 'Fullstack Responsive Interface Build'],
        duration: '3h 00m'
      }
    ]
  }

  // 2. iOS & Swift / SwiftUI
  if (textToMatch.includes('swift') || textToMatch.includes('swiftui') || (textToMatch.includes('ios') && !textToMatch.includes('react native'))) {
    return [
      {
        module: 'Module 1',
        title: 'Swift 5 & Language Fundamentals',
        lessons: ['Optionuals & Type Safety', 'Structs vs Classes', 'Protocols & Generics', 'Memory Management (ARC)'],
        duration: '3h 30m'
      },
      {
        module: 'Module 2',
        title: 'Declarative UI with SwiftUI',
        lessons: ['State & Binding Properties', 'View Composability & Modifiers', 'NavigationStack & Sheets', 'Custom Animations'],
        duration: '4h 15m'
      },
      {
        module: 'Module 3',
        title: 'CoreData & Offline Persistence',
        lessons: ['NSManagedObject Context', 'Fetch Requests & Predicates', 'Combine Framework Pipelines', 'Async/Await Networking'],
        duration: '3h 50m'
      },
      {
        module: 'Module 4',
        title: 'iOS App Store Release & CI/CD',
        lessons: ['App Store Connect Setup', 'TestFlight Beta Distribution', 'Provisioning Profiles & Signing', 'Xcode Cloud Automation'],
        duration: '2h 45m'
      }
    ]
  }

  // 3. Flutter & Dart
  if (textToMatch.includes('flutter') || textToMatch.includes('dart')) {
    return [
      {
        module: 'Module 1',
        title: 'Dart 3 Programming Essentials',
        lessons: ['Sound Null Safety', 'Object-Oriented Dart', 'Async Streams & Futures', 'Pattern Matching'],
        duration: '3h 20m'
      },
      {
        module: 'Module 2',
        title: 'Flutter Widget Tree & Custom UI',
        lessons: ['Stateless vs Stateful Widgets', 'Layout Mechanics (Row, Column, Stack)', 'Custom Painters & Animations', 'Material 3 Design Tokens'],
        duration: '4h 10m'
      },
      {
        module: 'Module 3',
        title: 'State Management with BLoC & Provider',
        lessons: ['Event-Driven Architecture (BLoC)', 'Provider & Riverpod Patterns', 'REST API Integration with Dio', 'Local Storage (Hive/Isar)'],
        duration: '4h 30m'
      },
      {
        module: 'Module 4',
        title: 'Firebase & Cross-Platform Release',
        lessons: ['Firebase Auth & Firestore', 'Push Notifications (FCM)', 'Android APK & iOS IPA Build', 'App Store Publishing'],
        duration: '3h 00m'
      }
    ]
  }

  // 4. React Native & Expo
  if (textToMatch.includes('react native') || textToMatch.includes('expo')) {
    return [
      {
        module: 'Module 1',
        title: 'React Native & Expo Router Foundations',
        lessons: ['Expo CLI Tooling', 'Core Native Components', 'File-Based Routing', 'StyleSheet & Native Flexbox'],
        duration: '3h 15m'
      },
      {
        module: 'Module 2',
        title: 'Native Device Features & State Management',
        lessons: ['Camera, Location & Sensors', 'AsyncStorage & SecureStore', 'Zustand & Context API', 'Custom Native Modules'],
        duration: '4h 00m'
      },
      {
        module: 'Module 3',
        title: 'Mobile UI Animations & Reanimated',
        lessons: ['React Native Reanimated 3', 'Gesture Handler Library', 'Smooth Scroll Animations', 'Performance Profiling'],
        duration: '3h 45m'
      },
      {
        module: 'Module 4',
        title: 'EAS Build & Store Publishing',
        lessons: ['Expo Application Services (EAS)', 'OTA (Over-the-Air) Updates', 'Apple Developer & Play Console', 'CI/CD Publishing'],
        duration: '2h 50m'
      }
    ]
  }

  // 5. Android & Kotlin
  if (textToMatch.includes('android') || textToMatch.includes('kotlin')) {
    return [
      {
        module: 'Module 1',
        title: 'Kotlin & Jetpack Compose UI Foundations',
        lessons: ['Kotlin Syntax & Null Safety', 'Declarative UI with Compose', 'State & Recomposition', 'Material 3 Themes'],
        duration: '3h 30m'
      },
      {
        module: 'Module 2',
        title: 'Android Architecture & State Management',
        lessons: ['ViewModels & LiveData', 'Coroutines & Asynchronous Flow', 'Navigation Component', 'Dependency Injection (Hilt)'],
        duration: '4h 15m'
      },
      {
        module: 'Module 3',
        title: 'Room Database & Offline Storage',
        lessons: ['Room DAOs & Entities', 'SQLite Querying', 'Repository Pattern', 'Offline-First Synchronization'],
        duration: '3h 45m'
      },
      {
        module: 'Module 4',
        title: 'REST API Integration & App Release',
        lessons: ['Retrofit & OkHttp Networking', 'JSON Parsing with Moshi', 'Google Play Store Signing', 'CI/CD Publishing'],
        duration: '2h 50m'
      }
    ]
  }

  // 6. System Design & Microservices
  if (textToMatch.includes('system design') || textToMatch.includes('distributed') || textToMatch.includes('microservices')) {
    return [
      {
        module: 'Module 1',
        title: 'High-Scale System Architecture & CAP Theorem',
        lessons: ['Scalability (Vertical vs Horizontal)', 'Load Balancers & Reverse Proxies', 'Consistent Hashing & Partitioning', 'CAP Theorem & PACELC'],
        duration: '3h 40m'
      },
      {
        module: 'Module 2',
        title: 'Database Sharding, Caching & Replication',
        lessons: ['Read Replicas & Master-Slave', 'Redis & Memcached Strategies', 'Database Sharding Patterns', 'Distributed Lock (Redlock)'],
        duration: '4h 30m'
      },
      {
        module: 'Module 3',
        title: 'Microservices & Event-Driven Architecture',
        lessons: ['API Gateways & Service Mesh', 'CQRS & Event Sourcing', 'Kafka & Message Queues', 'Circuit Breakers & Resilience'],
        duration: '4h 20m'
      },
      {
        module: 'Module 4',
        title: 'Real-World System Design Case Studies',
        lessons: ['Designing Uber / Ride-Sharing', 'Designing WhatsApp / Chat Systems', 'Designing YouTube / Video Streaming', 'System Design Interview Framework'],
        duration: '3h 15m'
      }
    ]
  }

  // 7. Data Engineering
  if (textToMatch.includes('data engineering') || textToMatch.includes('spark') || textToMatch.includes('kafka') || textToMatch.includes('airflow') || textToMatch.includes('etl') || textToMatch.includes('big data')) {
    return [
      {
        module: 'Module 1',
        title: 'Data Engineering Pipelines & Architecture',
        lessons: ['Batch vs Streaming Architectures', 'Data Lakehouse Patterns', 'PySpark DataFrame API', 'Distributed Storage (S3/HDFS)'],
        duration: '3h 40m'
      },
      {
        module: 'Module 2',
        title: 'Real-Time Event Streaming with Apache Kafka',
        lessons: ['Producers & Consumers', 'Topic Partitions & Retention', 'Kafka Connect Framework', 'Real-Time Analytics'],
        duration: '4h 30m'
      },
      {
        module: 'Module 3',
        title: 'Data Workflow Orchestration with Airflow',
        lessons: ['DAG Design & Task Operators', 'Backfilling & Sensors', 'Custom Airflow Plugins', 'Production Scheduling'],
        duration: '3h 50m'
      },
      {
        module: 'Module 4',
        title: 'Modern Cloud Data Warehousing',
        lessons: ['Snowflake Architecture', 'dbt Data Transformations', 'Data Quality Testing', 'Pipeline Monitoring'],
        duration: '2h 45m'
      }
    ]
  }

  // 8. Database & SQL
  if (textToMatch.includes('database') || textToMatch.includes('sql') || textToMatch.includes('postgres') || textToMatch.includes('mongo') || textToMatch.includes('redis')) {
    return [
      {
        module: 'Module 1',
        title: 'Relational Database Modeling & Advanced SQL',
        lessons: ['ER Diagrams & Normalization', 'Complex Window Functions', 'CTEs & Subqueries', 'Transaction Isolation Levels'],
        duration: '3h 20m'
      },
      {
        module: 'Module 2',
        title: 'PostgreSQL Performance & Query Optimization',
        lessons: ['B-Tree & GIN Indexing', 'EXPLAIN ANALYZE Deep Dive', 'Connection Pooling (PgBouncer)', 'VACUUM & Autovacuum'],
        duration: '4h 10m'
      },
      {
        module: 'Module 3',
        title: 'NoSQL Document Stores with MongoDB',
        lessons: ['Document Schema Design', 'Aggregation Framework', 'Sharding & Replica Sets', 'Atlas Cloud Deployment'],
        duration: '3h 35m'
      },
      {
        module: 'Module 4',
        title: 'In-Memory Caching Architecture with Redis',
        lessons: ['Data Structures (Hashes, Sets)', 'Cache Eviction Policies', 'Pub/Sub Messaging', 'Redis Cluster Setup'],
        duration: '2h 30m'
      }
    ]
  }

  // 9. Game Dev
  if (textToMatch.includes('game') || textToMatch.includes('unity') || textToMatch.includes('unreal') || textToMatch.includes('c++')) {
    return [
      {
        module: 'Module 1',
        title: 'Game Engine Architecture & C# Scripting',
        lessons: ['Vector Math & Trigonometry', 'Component Lifecycle', 'Input System API', 'Physics & Rigidbodies'],
        duration: '3h 45m'
      },
      {
        module: 'Module 2',
        title: '3D Gameplay Systems & Character Control',
        lessons: ['NavMesh Pathfinding', 'Animator State Machines', 'Inventory & Item Systems', 'Camera Controllers'],
        duration: '4h 40m'
      },
      {
        module: 'Module 3',
        title: 'Shaders, Lighting & Visual Effects',
        lessons: ['HLSL/GLSL Shader Graph', 'Particle Systems (VFX Graph)', 'Post-Processing Stacks', 'Audio Spatialization'],
        duration: '4h 00m'
      },
      {
        module: 'Module 4',
        title: 'Multiplayer Networking & Game Release',
        lessons: ['Client-Server Architecture', 'RPCs & Network Variables', 'Steamworks API Integration', 'Build Optimization'],
        duration: '3h 10m'
      }
    ]
  }

  // 10. UI/UX & Design Systems
  if (textToMatch.includes('figma') || textToMatch.includes('ui/ux') || textToMatch.includes('user experience') || textToMatch.includes('wireframe')) {
    return [
      {
        module: 'Module 1',
        title: 'UX Research, Personas & User Journeys',
        lessons: ['User Interview Techniques', 'Empathy Mapping & Personas', 'Information Architecture', 'User Flow Diagrams'],
        duration: '3h 10m'
      },
      {
        module: 'Module 2',
        title: 'Figma Mastery & Auto-Layout Component Systems',
        lessons: ['Grid Systems & Typography', 'Auto-Layout 5.0 Precision', 'Component Variants & Props', 'Design Token Variables'],
        duration: '4h 25m'
      },
      {
        module: 'Module 3',
        title: 'Interactive Prototyping & Micro-Interactions',
        lessons: ['Smart Animate Transitions', 'Component State Triggers', 'Micro-Animation Physics', 'Interactive Component Libraries'],
        duration: '3h 50m'
      },
      {
        module: 'Module 4',
        title: 'Design Systems & Developer Hand-off',
        lessons: ['Design System Documentation', 'Accessibility (WCAG 2.1)', 'Figma Dev Mode Export', 'Design Audit & Iteration'],
        duration: '2h 40m'
      }
    ]
  }

  // 11. Cloud & DevOps
  if (textToMatch.includes('cloud') || textToMatch.includes('devops') || textToMatch.includes('aws') || textToMatch.includes('docker') || textToMatch.includes('kubernetes') || textToMatch.includes('terraform')) {
    return [
      {
        module: 'Module 1',
        title: 'AWS Cloud Architecture & Core Services',
        lessons: ['VPC Subnets & Security Groups', 'EC2 & Auto-Scaling Groups', 'S3 Bucket Policies & Lifecycle', 'IAM Roles & Policies'],
        duration: '3h 30m'
      },
      {
        module: 'Module 2',
        title: 'Containerization with Docker',
        lessons: ['Dockerfile Multi-Stage Builds', 'Docker Compose Networking', 'Container Security Scanning', 'Registry Management'],
        duration: '4h 15m'
      },
      {
        module: 'Module 3',
        title: 'Kubernetes Cluster Orchestration',
        lessons: ['Deployments & StatefulSets', 'Services & Ingress Controllers', 'Helm Chart Management', 'Cluster Monitoring (Prometheus)'],
        duration: '4h 50m'
      },
      {
        module: 'Module 4',
        title: 'Infrastructure as Code & CI/CD Pipelines',
        lessons: ['Terraform Modules & State', 'GitHub Actions Workflows', 'Blue-Green Deployments', 'DevOps Capstone Project'],
        duration: '3h 20m'
      }
    ]
  }

  // 12. Cyber Security
  if (textToMatch.includes('cyber') || textToMatch.includes('security') || textToMatch.includes('ethical') || textToMatch.includes('hacking')) {
    return [
      {
        module: 'Module 1',
        title: 'Network Security & Wireshark Packet Inspection',
        lessons: ['TCP/IP Protocol Deep Dive', 'Packet Analysis with Wireshark', 'TLS/SSL Inspection', 'Firewall Rules'],
        duration: '3h 15m'
      },
      {
        module: 'Module 2',
        title: 'Ethical Hacking & Vulnerability Assessment',
        lessons: ['Reconnaissance & Nmap Scanning', 'Metasploit Exploitation', 'Privilege Escalation', 'Vulnerability Auditing'],
        duration: '4h 45m'
      },
      {
        module: 'Module 3',
        title: 'Reverse Engineering & Malware Analysis',
        lessons: ['Ghidra Binary Disassembly', 'Static & Dynamic Malware Analysis', 'Buffer Overflows', 'Unpacking Trojans'],
        duration: '5h 10m'
      },
      {
        module: 'Module 4',
        title: 'Digital Forensics & Incident Response',
        lessons: ['Memory Forensics & Volatility', 'Linux/Windows Log Auditing', 'Threat Hunting', 'DFIR Capstone Case'],
        duration: '3h 30m'
      }
    ]
  }

  // 13. AI / Machine Learning
  if (/\bai\b/.test(textToMatch) || textToMatch.includes('machine learning') || textToMatch.includes('deep learning') || textToMatch.includes('neural') || textToMatch.includes('pytorch') || textToMatch.includes('tensorflow') || textToMatch.includes('nlp')) {
    return [
      {
        module: 'Module 1',
        title: 'Neural Networks & Deep Learning Foundations',
        lessons: ['Linear Algebra & Matrices', 'Backpropagation & Loss', 'PyTorch Tensors', 'Building Your First MLP'],
        duration: '3h 00m'
      },
      {
        module: 'Module 2',
        title: 'Computer Vision & Convolutional Nets',
        lessons: ['Image Processing Filters', 'CNN Architectures (ResNet)', 'Object Detection YOLO', 'Segmentation Models'],
        duration: '4h 20m'
      },
      {
        module: 'Module 3',
        title: 'Transformers & Large Language Models',
        lessons: ['Self-Attention Mechanism', 'Transformer Encoders & Decoders', 'Fine-Tuning Llama 3', 'RAG Vector Search'],
        duration: '5h 30m'
      },
      {
        module: 'Module 4',
        title: 'Autonomous AI Agents & LangGraph',
        lessons: ['Agentic Workflows & Tool Call', 'LangGraph State Machines', 'Multi-Agent Teams', 'Production LLM Deployment'],
        duration: '3h 45m'
      }
    ]
  }

  // 14. Blockchain & Web3
  if (textToMatch.includes('blockchain') || textToMatch.includes('solidity') || textToMatch.includes('web3') || textToMatch.includes('crypto')) {
    return [
      {
        module: 'Module 1',
        title: 'Cryptographic Foundations & Blockchain Basics',
        lessons: ['Hashing & Merkle Trees', 'Elliptic Curve Cryptography', 'Consensus Mechanisms (PoW/PoS)', 'P2P Network Protocol'],
        duration: '3h 10m'
      },
      {
        module: 'Module 2',
        title: 'Solidity Smart Contract Development',
        lessons: ['Data Types & Mappings', 'Modifier & Event Patterns', 'ERC-20 & ERC-721 Standards', 'Hardhat Testing Suite'],
        duration: '4h 30m'
      },
      {
        module: 'Module 3',
        title: 'DeFi Protocol Architecture & Web3 Integration',
        lessons: ['Automated Market Makers (AMM)', 'Staking & Yield Mechanics', 'Ethers.js / Viem Integration', 'Oracle Feeds (Chainlink)'],
        duration: '4h 15m'
      },
      {
        module: 'Module 4',
        title: 'Smart Contract Auditing & Security',
        lessons: ['Reentrancy Attack Prevention', 'Front-Running & MEV Protection', 'Slither Static Analysis', 'Security Audit Capstone'],
        duration: '3h 40m'
      }
    ]
  }

  // Web Dev default
  return [
    {
      module: 'Module 1',
      title: 'Modern Web Architecture & TypeScript',
      lessons: ['TypeScript Interfaces & Types', 'HTML5 & CSS Grid Layouts', 'DOM Manipulation & Events', 'Async/Await & Fetch API'],
      duration: '3h 00m'
    },
    {
      module: 'Module 2',
      title: 'React 18 & State Management Masterclass',
      lessons: ['Custom Hooks & Reusable Components', 'Context API & Zustand', 'Tailwind CSS Utility Design', 'Performance Optimization'],
      duration: '4h 15m'
    },
    {
      module: 'Module 3',
      title: 'Fullstack Next.js 14 App Router & Backend',
      lessons: ['Server Components & Client Components', 'Server Actions & Mutations', 'Prisma ORM & PostgreSQL', 'Authentication & Middleware'],
      duration: '4h 45m'
    },
    {
      module: 'Module 4',
      title: 'Production Deployment & Cloud CI/CD',
      lessons: ['Vercel & Docker Deployment', 'Automated E2E Testing', 'Security & Rate Limiting', 'Fullstack Capstone Build'],
      duration: '3h 10m'
    }
  ]
}

export const CourseDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuthStore()

  const [course, setCourse] = useState<Product | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [enrolled, setEnrolled] = useState<boolean>(false)
  const [enrolling, setEnrolling] = useState<boolean>(false)
  const [activeModule, setActiveModule] = useState<number>(0)
  const [completedLessons, setCompletedLessons] = useState<Record<string, boolean>>({})

  const modulesData = getCategoryModules(course?.category || '', course?.title || '')

  useEffect(() => {
    const loadCourseAndEnrollment = async () => {
      setLoading(true)
      setEnrolled(false) // Always reset enrollment state on course change

      const [allProducts, myEvents] = await Promise.all([
        getProducts(),
        getMyEvents(150).catch(() => []),
      ])

      const found = allProducts.find((p) => p.id === id) || allProducts[0]
      setCourse(found)

      if (found && myEvents) {
        // Find the MOST RECENT enroll or unenroll event for this course
        const enrollmentEvents = myEvents.filter(evt => {
          const isThisCourse =
            (evt.product_id && String(evt.product_id).toLowerCase() === String(found.id).toLowerCase()) ||
            ((evt as any).metadata?.course_title && (evt as any).metadata.course_title.toLowerCase() === found.title.toLowerCase()) ||
            ((evt as any).event_metadata?.course_title && (evt as any).event_metadata.course_title.toLowerCase() === found.title.toLowerCase())

          const evtType = String(evt.event_type).toLowerCase()
          const isEnrollOrUnenroll =
            evtType === 'enroll' ||
            evtType === 're_enroll' ||
            evtType === 'enrollment' ||
            evtType === 'unenroll' ||
            evtType === 'drop_course'

          return isThisCourse && isEnrollOrUnenroll
        })

        if (enrollmentEvents.length > 0) {
          const latestEvt = enrollmentEvents[0]
          const latestType = String(latestEvt.event_type).toLowerCase()
          const isCurrentlyEnrolled =
            latestType === 'enroll' || latestType === 're_enroll' || latestType === 'enrollment'
          setEnrolled(isCurrentlyEnrolled)
        } else {
          setEnrolled(false)
        }
      } else {
        setEnrolled(false)
      }

      setLoading(false)

      if (user && found) {
        trackEvent({
          user_id: user.id,
          session_id: 'session-' + Date.now(),
          event_type: 'view_product',
          product_id: found.id,
          metadata: { course_title: found.title, category: found.category }
        })
      }
    }
    loadCourseAndEnrollment()
  }, [id, user])

  const startTimeRef = useRef<number>(Date.now())

  // Automatic Dwell Time Tracking
  useEffect(() => {
    if (!user || !course) return

    startTimeRef.current = Date.now()

    // Send initial view event with dwell time
    trackEvent({
      user_id: user.id,
      session_id: 'session-' + Date.now(),
      event_type: 'view_product',
      product_id: course.id,
      dwell_time: 5,
      metadata: { course_title: course.title, category: course.category, page_url: window.location.pathname },
      event_metadata: { course_title: course.title, category: course.category, page_url: window.location.pathname }
    }).catch(() => {})

    // Send periodic time_on_page dwell update every 10 seconds
    const interval = setInterval(() => {
      const elapsed = Math.max(5, Math.round((Date.now() - startTimeRef.current) / 1000))
      trackEvent({
        user_id: user.id,
        session_id: 'session-' + Date.now(),
        event_type: 'time_on_page',
        product_id: course.id,
        dwell_time: elapsed,
        metadata: { course_title: course.title, category: course.category, dwell_time: elapsed, page_url: window.location.pathname },
        event_metadata: { course_title: course.title, category: course.category, dwell_time: elapsed, page_url: window.location.pathname }
      }).catch(() => {})
    }, 10000)

    // Cleanup on page unmount / leave: send final total dwell time
    return () => {
      clearInterval(interval)
      const finalDwell = Math.max(5, Math.round((Date.now() - startTimeRef.current) / 1000))
      trackEvent({
        user_id: user.id,
        session_id: 'session-' + Date.now(),
        event_type: 'time_on_page',
        product_id: course.id,
        dwell_time: finalDwell,
        metadata: { course_title: course.title, category: course.category, dwell_time: finalDwell, page_url: window.location.pathname },
        event_metadata: { course_title: course.title, category: course.category, dwell_time: finalDwell, page_url: window.location.pathname }
      }).catch(() => {})
    }
  }, [course?.id, user?.id])

  const handleEnroll = async () => {
    if (!user || !course) return
    setEnrolling(true)

    // Use 'enroll' action for first-time enrollment so the BehaviorAgent
    // correctly counts it as a new enrollment, not a re-enrollment.
    const meta = { 
      course_title: course.title, 
      price: course.price, 
      category: course.category,
      action: 'enroll',
      enrolled_at: new Date().toISOString() 
    }

    await trackEvent({
      user_id: user.id,
      session_id: 'session-' + Date.now(),
      event_type: 'enroll',
      product_id: course.id,
      event_metadata: meta,
      metadata: meta
    })

    await refreshRecommendations().catch(() => {})

    setEnrolled(true)
    setEnrolling(false)
  }

  const handleUnenroll = async () => {
    if (!user || !course) return
    setEnrolling(true)

    const meta = {
      course_title: course.title,
      category: course.category,
      action: 'unenroll',
      unenrolled_at: new Date().toISOString()
    }

    await trackEvent({
      user_id: user.id,
      session_id: 'session-' + Date.now(),
      event_type: 'unenroll',
      product_id: course.id,
      event_metadata: meta,
      metadata: meta
    })

    await refreshRecommendations().catch(() => {})

    setEnrolled(false)
    setEnrolling(false)
  }

  const handleModuleSelect = async (moduleIdx: number, moduleObj: any) => {
    setActiveModule(moduleIdx)

    if (user && course) {
      const meta = {
        course_title: course.title,
        category: course.category,
        module_index: moduleIdx,
        module_title: moduleObj.title,
        action: 'module_watch',
        watched_at: new Date().toISOString()
      }

      await trackEvent({
        user_id: user.id,
        session_id: 'session-' + Date.now(),
        event_type: 'view_product',
        product_id: course.id,
        dwell_time: 15,
        metadata: meta,
        event_metadata: meta
      }).catch(() => {})

      await refreshRecommendations().catch(() => {})
    }
  }

  const toggleLessonCompleted = async (lessonKey: string, lessonTitle: string, moduleTitle: string, moduleIdx: number) => {
    const isNowDone = !completedLessons[lessonKey]
    const updatedLessons = { ...completedLessons, [lessonKey]: isNowDone }
    setCompletedLessons(updatedLessons)

    if (isNowDone && user && course) {
      const sessionId = 'session-' + Date.now()
      const lessonMeta = {
        course_title: course.title,
        category: course.category,
        module: moduleTitle,
        lesson: lessonTitle,
        action: 'lesson_complete',
        completed_at: new Date().toISOString()
      }

      await trackEvent({
        user_id: user.id,
        session_id: sessionId,
        event_type: 'lesson_complete',
        product_id: course.id,
        event_metadata: lessonMeta,
        metadata: lessonMeta
      }).catch(() => {})

      // Check if ALL lessons in this module are now completed → fire module_complete
      const currentModuleLessons = modulesData[moduleIdx].lessons
      const allModuleLessonsDone = currentModuleLessons.every((_, lIdx) => {
        const key = `mod-${moduleIdx}-l-${lIdx}`
        return updatedLessons[key]
      })

      if (allModuleLessonsDone) {
        const moduleMeta = {
          course_title: course.title,
          category: course.category,
          module: moduleTitle,
          module_index: moduleIdx,
          action: 'module_complete',
          completed_at: new Date().toISOString()
        }
        await trackEvent({
          user_id: user.id,
          session_id: sessionId,
          event_type: 'module_complete',
          product_id: course.id,
          event_metadata: moduleMeta,
          metadata: moduleMeta
        }).catch(() => {})
      }

      await refreshRecommendations().catch(() => {})
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    )
  }

  if (!course) return null

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Back link */}
        <Link to="/courses" className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-primary-600 mb-6 transition-colors">
          <HiArrowLeft className="w-4 h-4" /> Back to Catalog
        </Link>

        {/* Course Header Banner */}
        <div className="bg-gradient-to-r from-gray-900 via-indigo-950 to-primary-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-8 relative overflow-hidden">
          <div className="max-w-3xl space-y-4">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-primary-600/80 text-white text-xs font-semibold rounded-full backdrop-blur-md">
                {course.category}
              </span>
              <span className="text-xs text-primary-200 capitalize font-medium">
                Level: {course.difficulty_level.toLowerCase()} • {course.duration_hours || 15} hours
              </span>
              {enrolled && (
                <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 text-xs font-semibold rounded-full border border-emerald-400/30 flex items-center gap-1">
                  <HiBadgeCheck className="w-4 h-4" /> Enrolled (Full Access)
                </span>
              )}
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
              {course.title}
            </h1>

            <p className="text-gray-300 text-base leading-relaxed">
              {course.description}
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-2">
              {course.tags.map((tag) => (
                <span key={tag} className="text-xs bg-white/10 px-2.5 py-1 rounded-md text-primary-100 border border-white/10">
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Course Player / Modules */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* IF ENROLLED: Show Full Interactive Module Player & Learning Hub */}
            {enrolled ? (
              <div className="space-y-6">
                
                {/* Module Video Player Card */}
                {(() => {
                  const videoInfo = getYouTubeVideoInfo(course.category, activeModule, course.title)
                  return (
                    <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-gray-100 space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-xs font-bold text-primary-600 uppercase tracking-wider">
                            {modulesData[activeModule].module} Lecture • {videoInfo.channel}
                          </span>
                          <h2 className="text-xl font-bold text-gray-900 mt-1">
                            {modulesData[activeModule].title}
                          </h2>
                        </div>
                        <span className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full font-semibold">
                          {modulesData[activeModule].duration}
                        </span>
                      </div>

                      {/* Embedded Module Video Player */}
                      <div className="relative w-full rounded-2xl overflow-hidden shadow-lg aspect-video bg-black">
                        <iframe
                          className="absolute top-0 left-0 w-full h-full border-0"
                          src={videoInfo.embed}
                          title={`${modulesData[activeModule].title} Video`}
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                          referrerPolicy="strict-origin-when-cross-origin"
                          allowFullScreen
                        />
                      </div>

                      {/* Download Notes / Resources / YouTube Link */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 text-xs border-t border-gray-100">
                        <span className="text-emerald-700 font-semibold flex items-center gap-1">
                          <HiCheckCircle className="w-4 h-4 text-emerald-600" /> Full HD 1080p Video Unlocked
                        </span>
                        <div className="flex items-center gap-3">
                          <a
                            href={videoInfo.watch}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-red-700 font-bold flex items-center gap-1.5 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg border border-red-200/80 transition-colors"
                          >
                            <FaYoutube className="w-4 h-4 text-red-600" /> Watch on YouTube ↗
                          </a>
                          <button onClick={() => alert("Downloading module source code archive...")} className="text-gray-600 hover:text-primary-600 font-semibold flex items-center gap-1">
                            <HiCode className="w-4 h-4" /> Source Code
                          </button>
                          <button onClick={() => alert("Opening PDF lecture notes...")} className="text-gray-600 hover:text-primary-600 font-semibold flex items-center gap-1">
                            <HiDocumentText className="w-4 h-4" /> Lecture Notes
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })()}

                {/* Module Navigation Tabs & Lesson Checklist */}
                <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-gray-100 space-y-6">
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <HiBookmark className="w-5 h-5 text-primary-600" /> Course Modules & Lessons
                  </h3>

                  {/* Module Selector Tabs */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {modulesData.map((mod, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleModuleSelect(idx, mod)}
                        className={`p-3 rounded-xl text-left transition-all border ${
                          activeModule === idx
                            ? 'bg-primary-600 text-white border-primary-600 shadow-sm'
                            : 'bg-gray-50 hover:bg-gray-100 text-gray-700 border-gray-200'
                        }`}
                      >
                        <div className="text-[10px] font-extrabold uppercase opacity-80">{mod.module}</div>
                        <div className="text-xs font-bold truncate mt-0.5">{mod.title}</div>
                      </button>
                    ))}
                  </div>

                  {/* Lessons Checklist for Active Module */}
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                      {modulesData[activeModule].module} Lessons Checklist
                    </h4>

                    {modulesData[activeModule].lessons.map((lesson, lIdx) => {
                      const lessonKey = `mod-${activeModule}-l-${lIdx}`
                      const isDone = !!completedLessons[lessonKey]
                      return (
                        <div
                          key={lIdx}
                          onClick={() => toggleLessonCompleted(lessonKey, lesson, modulesData[activeModule].title, activeModule)}
                          className={`p-3.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                            isDone 
                              ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950' 
                              : 'bg-gray-50 border-gray-100 hover:border-gray-200 text-gray-800'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={isDone}
                              onChange={() => {}} // Handled by parent div
                              className="w-4 h-4 text-emerald-600 rounded focus:ring-emerald-500 cursor-pointer"
                            />
                            <span className={`text-sm font-semibold ${isDone ? 'line-through opacity-75' : ''}`}>
                              {lIdx + 1}. {lesson}
                            </span>
                          </div>
                          <span className="text-xs text-gray-400 font-medium">35 min</span>
                        </div>
                      )
                    })}
                  </div>
                </div>

              </div>
            ) : (
              /* IF NOT ENROLLED: Show Locked Teaser & Course Overview */
              <div className="space-y-8">
                
                {/* Locked Video Preview Teaser Banner */}
                <div className="bg-gradient-to-br from-amber-500/10 via-amber-50 to-orange-50 border border-amber-200/80 rounded-3xl p-8 text-amber-950 shadow-sm relative overflow-hidden space-y-4">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-amber-500 text-white rounded-2xl flex items-center justify-center shrink-0 shadow-md">
                      <HiLockClosed className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-amber-950">
                        Course Video Modules & Lessons Locked
                      </h3>
                      <p className="text-sm text-amber-900 mt-1 leading-relaxed max-w-xl">
                        Enroll in this course to unlock all 4 video modules, HD lecture streams, downloadable source code, and step-by-step project exercises.
                      </p>
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={handleEnroll}
                      disabled={enrolling}
                      className="px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white font-bold text-sm rounded-xl shadow-md transition-all inline-flex items-center gap-2"
                    >
                      <HiSparkles className="w-4 h-4 text-amber-200" />
                      {enrolling ? 'Unlocking Course…' : 'Enroll Now to Unlock Full Course'}
                    </button>
                  </div>
                </div>

                {/* What You'll Learn Overview */}
                <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-gray-100">
                  <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <HiSparkles className="w-5 h-5 text-primary-600" /> What You'll Learn
                  </h2>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-gray-700">
                    <li className="flex items-start gap-2">
                      <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Hands-on project-based curriculum
                    </li>
                    <li className="flex items-start gap-2">
                      <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Industry best practices & patterns
                    </li>
                    <li className="flex items-start gap-2">
                      <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Personalized AI learning feedback
                    </li>
                    <li className="flex items-start gap-2">
                      <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Full access to source code & notes
                    </li>
                  </ul>
                </div>

                {/* Locked Modules Teaser List */}
                <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-gray-100">
                  <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                    <HiBookmark className="w-5 h-5 text-primary-600" /> Course Curriculum Teaser
                  </h2>
                  <div className="space-y-4">
                    {modulesData.map((m, idx) => (
                      <div key={idx} className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-between opacity-80">
                        <div className="flex items-center gap-3">
                          <HiLockClosed className="w-4 h-4 text-amber-600" />
                          <div>
                            <span className="text-xs font-semibold text-primary-600 uppercase tracking-wider">{m.module}</span>
                            <h4 className="text-sm font-bold text-gray-900 mt-0.5">{m.title}</h4>
                          </div>
                        </div>
                        <span className="text-xs text-gray-500">{m.duration}</span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            )}

          </div>

          {/* Right Column: Enrollment Card */}
          <div>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 sticky top-24 space-y-6">
              
              <div className="text-center pb-4 border-b border-gray-100">
                <div className="text-3xl font-extrabold text-gray-900">${course.price}</div>
                <div className="text-xs text-emerald-600 font-semibold mt-1">Full Lifetime Access</div>
              </div>

              {enrolled ? (
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 text-center text-emerald-900 animate-fade-in space-y-3">
                  <HiBadgeCheck className="w-10 h-10 text-emerald-600 mx-auto" />
                  <div className="font-bold text-base">Enrolled in Course</div>
                  <div className="text-xs text-emerald-700">Full video lectures, module tabs, and notes unlocked on the left!</div>
                  <button
                    onClick={handleUnenroll}
                    disabled={enrolling}
                    className="w-full py-2 mt-1 border border-red-300 text-red-600 hover:bg-red-50 text-xs font-semibold rounded-lg transition-all disabled:opacity-50"
                  >
                    {enrolling ? 'Processing...' : 'Unenroll from Course'}
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleEnroll}
                  disabled={enrolling}
                  className="w-full py-4 bg-primary-600 hover:bg-primary-700 text-white font-bold text-sm rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {enrolling ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Enrolling...</span>
                    </>
                  ) : (
                    <>
                      <span>Enroll Now →</span>
                    </>
                  )}
                </button>
              )}

              <div className="space-y-3 text-xs text-gray-600 border-t border-gray-100 pt-4">
                <div className="flex items-center gap-2">
                  <HiClock className="w-4 h-4 text-gray-400" />
                  <span>{course.duration_hours || 15} hours on-demand content</span>
                </div>
                <div className="flex items-center gap-2">
                  <HiAcademicCap className="w-4 h-4 text-gray-400" />
                  <span>Access on mobile and desktop</span>
                </div>
                <div className="flex items-center gap-2">
                  <HiBadgeCheck className="w-4 h-4 text-gray-400" />
                  <span>Certificate of completion</span>
                </div>
              </div>

            </div>
          </div>

        </div>

      </main>
    </div>
  )
}

export default CourseDetailPage
