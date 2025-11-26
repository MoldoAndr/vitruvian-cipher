export const CONFIG = {
    passwordChecker: {
        baseUrl: 'http://localhost:9000',
        endpoints: {
            health: '/health',
            score: '/score'
        }
    },
    theorySpecialist: {
        baseUrl: 'http://localhost:8100',
        endpoints: {
            health: '/health',
            generate: '/generate',
            ingest: '/ingest',
            conversations: '/conversations'
        }
    },
    choiceMaker: {
        baseUrl: 'http://localhost:8081',
        endpoints: {
            health: '/health',
            extract: '/predict'
        }
    }
};
