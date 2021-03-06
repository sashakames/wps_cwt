import logging
logger = logging.getLogger('celery.task')
from celery import Task
import cdtime

def get_cdtime_units( unit_spec ):
    us =  unit_spec.lower()
    if us.startswith('s'): return cdtime.Second
    if us.startswith('min'): return cdtime.Minute
    if us.startswith('h'): return cdtime.Hour
    if us.startswith('d'): return cdtime.Day
    if us.startswith('w'): return cdtime.Week
    if us.startswith('mon'): return cdtime.Month
    if us.startswith('y'): return cdtime.Year

class DomainBasedTask(Task):

    abstract = True
    _DomainCache = {}

    def __init__(self):
        pass

    @classmethod
    def createDomain(cls, partIndex, domainSpec ):
        domain = Domain( domainSpec )
        id = cls.generateDomainId( domainSpec )
        cls._DomainCache[ id ] = domain
        logger.info( "Create domain '%s', Domain Cache: %s " % ( id, str( cls._DomainCache ) ) )
        return id

    def __repr__(self):
        return "DomainBasedTask ( Cache: %s )" % str( self._DomainCache )

    @classmethod
    def generateDomainId(cls, domainSpec ):
        return domainSpec['id']

    @classmethod
    def getDomain(cls, domainId ):
        logger.info( "Get domain '%s', Domain Cache: %s " % ( domainId, str( cls._DomainCache ) ) )
        return cls._DomainCache.get( domainId, None )

    @classmethod
    def removeDomain( cls, domainId ):
        try:
            del cls._DomainCache[domainId]
        except KeyError:
            logger.error( "Attempt to delete non-existent domain: %s" % ( domainId ) )


class Domain(object):

    def __init__(self, spec ):
        self.id = spec['id']
        self.pIndex = spec['pIndex']
        self.roi = spec.get( 'roi', None )
        self.time = spec.get( 'time', None )
        self.grid = spec.get( 'grid', None )
        self.variables = {}
        logger.info( 'Create Domain[%d]: spec: %s' % (self.pIndex, str(spec) ) )

    def __repr__(self):
        return "Domain[%s] { roi: %s, grid: %s, time: %s } ( Variables: %s )" % ( self.id, self.roi, self.grid, self.time, self.variables.keys() )

    def add_variable( self, varId, variable, **args ):
        if self.time <> None:
            data_start = self.time['start'].split('-')
            part_time_step = self.time.get('step',1)
            part_time_units = get_cdtime_units( self.time['units'] )
            data_start_ct = cdtime.comptime( *[int(tok) for tok in data_start]  )
            partition_start_ct = data_start_ct.add( self.pIndex*part_time_step, part_time_units )
            partition_end_ct = partition_start_ct.add( part_time_step, part_time_units )
            logger.info( 'Domain[%d]: addVariable: %s -> %s' % (self.pIndex, str(partition_start_ct), str(partition_end_ct) ))
            part_variable = variable( time=( partition_start_ct, partition_end_ct, 'co') )
            self.variables[varId] = part_variable

    def remove_variable( self, varId ):
        try:
            del self.variables[varId]
        except KeyError:
            logger.error( "Attempt to delete non-existent variable '%s' in domain '%s'" % ( varId, self.id ) )
