
from typing import NamedTuple
from aws_cdk import (
    aws_apigateway,
    aws_cloudfront,
    aws_route53,
    aws_route53_targets,
    core
)


class Domains:
    def __init__(self, stage: str):

        stage = stage.lower()
        if stage == 'prod':
            self.stage = ''
        else:
            # We can use sub-domains with NS records if we replace this
            # with 'stage.' and point the domains in the prod account
            # at the beta account nameservers.
            self.stage = f'{stage}-'

        self.api = self.domain('api')
        self.visit = self.domain('visit')
        self.maintenance = self.domain('maintenance')
        self.admin = self.domain('admin')

    def domain(self, prefix: str) -> str:
        # todo: to expand to more schools or spaces, modify this
        return f'{self.stage}{prefix}.cumaker.space'


class MakerspaceDns(core.Stack):
    """
    Register the DNS used by the portions of the makerspace website owned by
    the capstone in Route53.

    The DNS for the rest of the makerspace is in Gandi, where we have a
    record delegating to the Route53 nameservers created by these zones.

    The biggest benefit of having Route53 manage the DNS for the maintenance
    and visitor login apps is that we can handle the TLS certs in AWS with
    fewer steps.
    """

    def __init__(self, scope: core.Construct,
                 stage: str, *, env: core.Environment):
        super().__init__(scope, f'MakerspaceDns-{stage}', env=env)

        self.domains = Domains(stage)

        self.visitors_zone()

        self.api_zone()

        self.maintenance_zone()

        # todo: deprecate this
        self.admin_zone()

    def visitors_zone(self):

        self.visit = aws_route53.PublicHostedZone(self, 'visit',
                                                  zone_name=self.domains.visit)

    def api_zone(self):

        self.api = aws_route53.PublicHostedZone(self, 'api',
                                                zone_name=self.domains.api)

    def maintenance_zone(self):

        aws_route53.PublicHostedZone(self, 'maintenance',
                                     zone_name=self.domains.maintenance)

    def admin_zone(self):

        aws_route53.PublicHostedZone(self, 'admin',
                                     zone_name=self.domains.admin)


class MakerspaceDnsRecords(core.Stack):

    def __init__(self, scope: core.Construct,
                 stage: str,
                 *,
                 env: core.Environment,
                 zones: MakerspaceDns,
                 api_gateway: aws_apigateway.RestApi,
                 visit_distribution: aws_cloudfront.Distribution):

        id = f'MakerspaceDnsRecords-{stage}'
        super().__init__(scope, id, env=env)

        self.zones = zones

        self.api_record(api_gateway)

        self.visit_record(visit_distribution)

    def api_record(self, api_gateway: aws_apigateway.RestApi):

        aws_route53.ARecord(self, 'ApiRecord',
                            zone=self.zones.api,
                            target=aws_route53.RecordTarget(
                                alias_target=aws_route53_targets.ApiGatewayDomain(
                                    api_gateway.domain_name)))

    def visit_record(self, visit: aws_cloudfront.Distribution):

        aws_route53.ARecord(self, 'VisitRecord',
                            zone=self.zones.visit,
                            target=aws_route53.RecordTarget(
                                alias_target=aws_route53_targets.CloudFrontTarget(
                                    distribution=visit)))
