# Description review — exploratory, not a certified accuracy score

12 frozen VRSBench evaluation images. Review by the coding assistant using images, model outputs and official reference captions; no independent human adjudicator. These cases are now development evidence. Do not report a human-validated caption accuracy percentage.

| Image | Finding | Category |
|---|---|---|
| P1598_0050.png | Airport context mentioned; two aircraft and roundabout omitted. Calling trees green is not supported by the grayscale input. | Omission; unsupported colour |
| P1390_0090.png | Aircraft presence captured; ground/runway context and layout largely omitted. | Sparse but core object supported |
| P0110_0015.png | Model calls the long structure a ship; reference calls it a harbor. Visual inspection supports a long fixed structure but does not certify its identity. | Disputed object identity; human review needed |
| P1377_0054.png | Houses and swimming pools captured; road, vehicles and vegetation not described. | Partial coverage |
| 10086_0000.png | Baseball field and surrounding grass/trees captured. Organized-game use and suburban/semi-rural context are inferred, not established. | Unsupported contextual claims |
| 08078_0000.png | Water and surrounding trees captured; dam feature omitted. | Major-feature omission |
| P8656_0106.png | Building/roof captured; roads beside it are not clearly established in the crop. | Possible unsupported feature; review needed |
| P2645_0012.png | Model describes railways, buildings and greenery. These match visible tracks better than the reference airport/ship description. Recreational-use inference remains unsupported. | Reference caption disputed; do not score by caption agreement alone |
| 06739_0000.png | Aircraft identified; two-plane count can include a partial aircraft at the right edge. Ground-service detail omitted. | Count sensitive to crop boundary; partial coverage |
| P0217_0000.png | Two planes and grass/tarmac context captured; both aircraft are partially cropped. | Broadly supported description |
| P1323_0020.png | River/bank context captured; bridges omitted and green colour cannot be established from grayscale. | Omission; unsupported colour |
| 08284_0000.png | Buildings/trees captured; prominent smoke plume and industrial detail omitted. | Major-feature omission |