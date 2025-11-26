const DEFAULT_AGENTS = [
    {
        name: "cyberchef",
        envVar: "CYBERCHEF_URL",
        defaultUrl: "http://cyberchef:8080/detect"
    },
    {
        name: "dcode_fr",
        envVar: "DCODE_URL",
        defaultUrl: "http://dcode_fr:8081/detect"
    }
];

export function loadAgents() {
    return DEFAULT_AGENTS
        .map((agent) => ({
            name: agent.name,
            url: process.env[agent.envVar] ?? agent.defaultUrl
        }))
        .filter((agent) => Boolean(agent.url));
}
