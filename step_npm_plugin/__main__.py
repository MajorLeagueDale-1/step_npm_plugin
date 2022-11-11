from step_npm_plugin.core import app, args, settings


if __name__ == '__main__':
    parser = args.parser.parse_args()

    config = settings.AppConfig(parser)
    app.run(config)
