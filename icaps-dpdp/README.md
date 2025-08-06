# Dynamic Vehicle Routing Problem

Math Project + Szakdolgozat

## Project

## Links

[Math Project - Dinamikus jármű útvonaltervezés](https://math-projects.elte.hu/projects/topic/191/)

[DPDP webpage](https://competition.huaweicloud.com/information/1000041411/circumstance)

[sci-hub](https://sci-hub.se/)
- ELTE hálózatról böngészve a legtöbb cikk letölthető. Ha valami mégsem, akkor ez egy jó kalóz oldal. Persze, itt sincs fent minden.
- Érdemes a doi azonosítót (pl.: ```10.1016/j.ejor.2021.07.014```) megadni neki, mert a cím alapján néha nem találja meg a cikket.

[The Python-MIP package](https://www.python-mip.com/)

## Literature

### DPDP Competition

[Cai, J., Zhu, Q., & Lin, Q. (2022). Variable neighborhood search for a new practical dynamic pickup and delivery problem. Swarm and Evolutionary Computation, 75, 101182.](https://www.sciencedirect.com/science/article/pii/S2210650222001493)
- Az első helyezett csapat algoritmusa.

[Cai, J., Zhu, Q., Lin, Q., Li, J., Chen, J., & Ming, Z. (2022, August). An Efficient Multi-objective Evolutionary Algorithm for a Practical Dynamic Pickup and Delivery Problem. In International Conference on Intelligent Computing (pp. 27-40). Cham: Springer International Publishing.](https://link.springer.com/chapter/10.1007/978-3-031-13870-6_3)

[Cai, J., Zhu, Q., Lin, Q., Ma, L., Li, J., & Ming, Z. (2023). A survey of dynamic pickup and delivery problems. Neurocomputing, 126631.](https://www.sciencedirect.com/science/article/pii/S0925231223007543)

[Du, J., Zhang, Z., Wang, X., & Lau, H. C. (2023). A hierarchical optimization approach for dynamic pickup and delivery problem with LIFO constraints. Transportation Research Part E: Logistics and Transportation Review, 175, 103131.](https://www.sciencedirect.com/science/article/pii/S1366554523001199)

### Dynamic Vehicle Routing

[Soeffker, N., Ulmer, M. W., & Mattfeld, D. C. (2022). *Stochastic dynamic vehicle routing in the light of prescriptive analytics: A review*. European Journal of Operational Research, 298(3), 801-820.](https://www.sciencedirect.com/science/article/pii/S0377221721006093)

- Markov-féle döntési eljárás

# Notes

- A késés szempontjából a delivery factory-ba való érkezés időpontja számít (az ottani várakozás, dokkolás, lepakolás már nem)
- A carrying items lista azonnal frissül, amikor a jármű megérkezik egy factory-ba: amit ott kell letennie, eltűnik a listáról, amit ott kell felvennie, megjelenik a listán
- A jármű aktuális destination-jéhez tartozó pickup-lista módosítható. Csak a célállomás nem módosítható, ha a jármű már úton van
- Lehet üresen is utaztatni a járműveket, de be fognak dokkolni minden állomáson
- Lehet várakoztatni egy járművet akkor is, ha van csomagja, de 4 órán belül mozgatni kell a csomagot (az order item-eknek meg kell jelenniük az inputban)
