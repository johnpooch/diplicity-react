import { mergeQueries } from "./common";
import { useGetOptionsQuery } from "./useGetOptionsQuery";
import { useGetVariantQuery } from "./useGetVariantQuery";

const useListHydratedOptionsQuery = (gameId: string) => {

    const getVariantQuery = useGetVariantQuery(gameId);
    const listOptionsQuery = useGetOptionsQuery(gameId);

    const mergedQuery = mergeQueries([getVariantQuery, listOptionsQuery], (variant, options) => {
        const transformOptions = (innerOptions: typeof options) => {
            const transformedOptions = {} as Record<string, typeof options[string]>;

            Object.entries(innerOptions).forEach(([key, value]) => {
                if (value.Type === "Province") {
                    const longName = variant.ProvinceLongNames[key];
                    transformedOptions[key] = {
                        ...value,
                        Name: longName,
                        Next: transformOptions(value.Next)
                    };
                } else {
                    transformedOptions[key] = {
                        ...value,
                        Next: transformOptions(value.Next)
                    };
                }
            });

            return transformedOptions;
        };

        return transformOptions(options);
    });

    return mergedQuery;
};

export { useListHydratedOptionsQuery };

// Example `options` object:
// {
//   "nap": {
//     "Type": "Province",
//     "Next": {
//       "Hold": {
//         "Type": "OrderType",
//         "Next": {
//           "nap": {
//             "Type": "SrcProvince",
//             "Next": {}
//           }
//         }
//       },
//       "Move": {
//         "Type": "OrderType",
//         "Next": {
//           "nap": {
//             "Type": "SrcProvince",
//             "Next": {
//               "apu": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "ion": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "rom": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "tys": {
//                 "Type": "Province",
//                 "Next": {}
//               }
//             }
//           }
//         }
//       },
//       "Support": {
//         "Type": "OrderType",
//         "Next": {
//           "nap": {
//             "Type": "SrcProvince",
//             "Next": {
//               "rom": {
//                 "Type": "Province",
//                 "Next": {
//                   "apu": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "rom": {
//                     "Type": "Province",
//                     "Next": {}
//                   }
//                 }
//               },
//               "ven": {
//                 "Type": "Province",
//                 "Next": {
//                   "apu": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "rom": {
//                     "Type": "Province",
//                     "Next": {}
//                   }
//                 }
//               }
//             }
//           }
//         }
//       }
//     }
//   },
//   "rom": {
//     "Type": "Province",
//     "Next": {
//       "Hold": {
//         "Type": "OrderType",
//         "Next": {
//           "rom": {
//             "Type": "SrcProvince",
//             "Next": {}
//           }
//         }
//       },
//       "Move": {
//         "Type": "OrderType",
//         "Next": {
//           "rom": {
//             "Type": "SrcProvince",
//             "Next": {
//               "apu": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "nap": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "tus": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "ven": {
//                 "Type": "Province",
//                 "Next": {}
//               }
//             }
//           }
//         }
//       },
//       "Support": {
//         "Type": "OrderType",
//         "Next": {
//           "rom": {
//             "Type": "SrcProvince",
//             "Next": {
//               "nap": {
//                 "Type": "Province",
//                 "Next": {
//                   "apu": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "nap": {
//                     "Type": "Province",
//                     "Next": {}
//                   }
//                 }
//               },
//               "ven": {
//                 "Type": "Province",
//                 "Next": {
//                   "apu": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "tus": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "ven": {
//                     "Type": "Province",
//                     "Next": {}
//                   }
//                 }
//               }
//             }
//           }
//         }
//       }
//     }
//   },
//   "ven": {
//     "Type": "Province",
//     "Next": {
//       "Hold": {
//         "Type": "OrderType",
//         "Next": {
//           "ven": {
//             "Type": "SrcProvince",
//             "Next": {}
//           }
//         }
//       },
//       "Move": {
//         "Type": "OrderType",
//         "Next": {
//           "ven": {
//             "Type": "SrcProvince",
//             "Next": {
//               "apu": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "pie": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "rom": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "tri": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "tus": {
//                 "Type": "Province",
//                 "Next": {}
//               },
//               "tyr": {
//                 "Type": "Province",
//                 "Next": {}
//               }
//             }
//           }
//         }
//       },
//       "Support": {
//         "Type": "OrderType",
//         "Next": {
//           "ven": {
//             "Type": "SrcProvince",
//             "Next": {
//               "mun": {
//                 "Type": "Province",
//                 "Next": {
//                   "tyr": {
//                     "Type": "Province",
//                     "Next": {}
//                   }
//                 }
//               },
//               "nap": {
//                 "Type": "Province",
//                 "Next": {
//                   "apu": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "rom": {
//                     "Type": "Province",
//                     "Next": {}
//                   }
//                 }
//               },
//               "rom": {
//                 "Type": "Province",
//                 "Next": {
//                   "apu": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "rom": {
//                     "Type": "Province",
//                     "Next": {}
//                   },
//                   "tus": {
//                     "Type": "Province",
//                     "Next": {}
//                   }
//                 }
//               }
//             }
//           }
//         }
//       }
//     }
//   }
// }