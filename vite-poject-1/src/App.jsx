import React, { useState } from 'react'
import './App.css'
import { TwitterFollowCard } from './TwitterFollowCard'

const users = [
{
    userName: 'x.com',
    name : 'aplicacion x',
    isFollowing: true 
},
{
    userName: 'Facebook.com',
    name: 'aplicacion facebook',
    isFollowing: false
},
{
    userName: 'Reddit.com',
    name : 'aplicacion Reddit',
    isFollowing: true
}, 
{
    userName: 'youtube.com',
    name: 'aplicacion Youtube',
    isFollowing: false
}
]

export function App () {

    return(
        <section className='App'>
            {
                users.map(user =>  {
                    const {userName, name, isFollowing} = user
                    return (
                        <TwitterFollowCard
                            key={userName}
                            userName={userName}
                            initialIsFollowing={isFollowing}
                        >
                            {name}
                        </TwitterFollowCard>
                    )
                })
            }
        </section>
    )
}
