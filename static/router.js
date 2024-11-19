import home from "./components/home.js"



const routes = [
    {path:'/', component: home},
]

export default VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes,
})