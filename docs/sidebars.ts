import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  userSidebar: [
    'intro',
    {
      type: 'category',
      label: 'User Guide',
      collapsed: false,
      items: [
        'user/getting-started',
        'user/faq',
      ],
    },
  ],
  technicalSidebar: [
    {
      type: 'category',
      label: 'Overview',
      collapsed: false,
      items: [
        'technical/overview',
        'technical/installation',
        'technical/architecture',
      ],
    },
    {
      type: 'category',
      label: 'API',
      collapsed: false,
      items: [
        'technical/api/overview',
        'technical/api/authentication',
        'technical/api/endpoints',
      ],
    },
    {
      type: 'category',
      label: 'Frontend',
      collapsed: true,
      items: [
        'technical/frontend/overview',
      ],
    },
    {
      type: 'category',
      label: 'Docker',
      collapsed: true,
      items: [
        'technical/docker/overview',
        'technical/docker/services',
        'technical/docker/development',
      ],
    },
    {
      type: 'category',
      label: 'Database',
      collapsed: true,
      items: [
        'technical/database/overview',
        'technical/database/models',
      ],
    },
  ],
};

export default sidebars;
