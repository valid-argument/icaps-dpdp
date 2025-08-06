# ICAPS-DPDP

## The Dynamic Pickup and Delivery Problem | ICAPS 2021 Competition

[Conference webpage](https://icaps21.icaps-conference.org/Competitions/)

[Competition webpage](https://competition.huaweicloud.com/information/1000041411/circumstance)

## About the project

See my [thesis](https://www.math.elte.hu/thesisupload/thesisfiles/2024msc_alkmat2y-kzje3n.pdf) for detailed information about the project and the algorithms used (in Hungarian)

Keywords: Dynamic Vehicle Routing Problem (DVRP), Dynamic Pickup and Delivery Problem (DPDP), Variable Neighborhood Search (VNS)

## How to use

**Simply run** `main.py`.

**To modify the problem instance**, update the `selected_instances` variable in `src/conf/configs.py`.

**To switch the solver algorithm**, update the import of the `scheduling` function in `main_algorithm.py` to reference a different module from the `algorithm` directory.
