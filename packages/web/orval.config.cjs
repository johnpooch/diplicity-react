module.exports = {
  diplicity: {
    input: '../../service/openapi-schema.yaml',
    output: {
      mode: 'single',
      target: './src/api/generated/endpoints.ts',
      client: 'react-query',
      override: {
        query: {
          useSuspenseQuery: true,
        },
        mutator: {
          path: './src/api/axiosInstance.ts',
          name: 'customInstance',
        },
        operations: {
          gamesList: {
            mock: {
              properties: () => ({
                '[].status': () => faker.helpers.arrayElement(['active', 'pending', 'completed']),
                '[].variantId': () => faker.helpers.arrayElement(['Classical', 'Hundred']),
              }),
            },
          },
          variantsList: {
            mock: {
              data: () => [
                {
                  id: 'Classical',
                  name: 'Classical Diplomacy',
                  description: 'The original Diplomacy game',
                  author: 'Allan B. Calhamer',
                  nations: [
                    { name: 'Austria', color: '#FF0000' },
                    { name: 'England', color: '#0000FF' },
                    { name: 'France', color: '#00FFFF' },
                    { name: 'Germany', color: '#000000' },
                    { name: 'Italy', color: '#00FF00' },
                    { name: 'Russia', color: '#FFFFFF' },
                    { name: 'Turkey', color: '#FFFF00' },
                  ],
                  provinces: [],
                  templatePhase: {
                    id: 1,
                    ordinal: 1,
                    season: 'Spring',
                    year: 1901,
                    name: 'Spring 1901 Movement',
                    type: 'Movement',
                    remainingTime: 0,
                    scheduledResolution: '1901-01-01T00:00:00Z',
                    status: 'template',
                    units: [],
                    supplyCenters: [],
                  },
                },
                {
                  id: 'italy-vs-germany',
                  name: 'Italy vs Germany',
                  description: 'A 2-player variant',
                  author: 'Unknown',
                  nations: [
                    { name: 'Italy', color: '#00FF00' },
                    { name: 'Germany', color: '#000000' },
                  ],
                  provinces: [],
                  templatePhase: {
                    id: 2,
                    ordinal: 1,
                    season: 'Spring',
                    year: 1901,
                    name: 'Spring 1901 Movement',
                    type: 'Movement',
                    remainingTime: 0,
                    scheduledResolution: '1901-01-01T00:00:00Z',
                    status: 'template',
                    units: [],
                    supplyCenters: [],
                  },
                },
              ]
            },
          },
        },
      },
      mock: {
        delay: 80,
      },
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
};
