import { useState } from "react"


export function TwitterFollowCard ({ children, userName, initialIsFollowing}) {
    const imageSrc = 'https://unavatar.io/google/${userName}'

    console.log('[TwitterFollowCard] render with userName: ', userName)

    const [isFollowing, setIsFollowing ] = useState(initialIsFollowing)

    const text = isFollowing ? 'Siguiendo' : 'Seguir'
    const buttonClassName = isFollowing 
    ? 'tw-followCard-button is-following' 
    : 'tw-followCard-button'

    const handleClick = () => { 
        setIsFollowing(!isFollowing)
    }

    return (
        <article className='tw-followCard'>
            <header className='tw-followCard-header'>
                <img 
                className='tw-followCard-avatar'
                alt="El avatar de Reddit"
                src= {`https://unavatar.io/google/${userName}`} />
                <div className='tw-followCard-info'>
                    <span>{children}</span>
                    <span className='tw-followCard-infoUserName'>@{userName}</span>
                </div>
            </header>

            <aside>
                <button className={buttonClassName} onClick={handleClick}>
                    <span className="tw-followCard-text">{text}</span>
                    <span className='tw-followCard-stopFollow'>Dejar de seguir</span>
                </button>
            </aside>
        </article>
    )

}

/* Hay 2 formas de poder llamar un parametro con la src
una es src={'https://unavatar.io/google/${userName}'} lo
cual es correcto pero la otra forma es evaluando la funcion
antes y declarando la constante imageSrc */ 

/*Esta es la forma en la que puedes editar los estilos
de los elementos directamnete, no es la indicada, pero
en react native asi se hace*/
/*<article style ={{ display: 'flex', alignItems: 'center',
color:'#fff'}}></article>*/

/* Con console.log puedes ver en la consola de inpeccion en la app
lo que se esta devolviendo */

/* A esto se le conoce como ternaria const text = isFollowing ? 'Siguiendo' : 'Seguir' 
y es como hacer un if pero en corto
 */

/* En jsx para poder usar React.Fragment hay 2 opciones
una la puedes usar usando <React.Fracment>...<React.Fragment/>
o simplemente usando < >...< /> y listo.
*/
/*Con cosnol.log('render whit ...', ...) puedo ver en la consola
de safari cuantas veces se ah renderisado un elemento*/

//Se pueden agregar comentarios a lo largo del cogigo
//De esta manera
/* Segunda manera */
{/** Y tambien de esta manera para cuando se necesiten comentarios
    dentro del area de renderizacion (Return) */}