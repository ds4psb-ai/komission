"""
Viral Pattern Optimizer - GA/RL Agent for Optimal Pattern Sequence Discovery
"과거 성공 데이터를 기반으로 최적의 바이럴 패턴 시퀀스 탐색"
"""
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from app.schemas.viral_codebook import VisualPatternCode, AudioPatternCode, SemanticIntent


@dataclass
class PatternGene:
    """단일 패턴 유전자 (Viral Mosaic Tile 기반)"""
    visual: VisualPatternCode
    audio: AudioPatternCode
    semantic: SemanticIntent
    
    def mutate(self, mutation_rate: float = 0.1) -> "PatternGene":
        """돌연변이 적용"""
        new_gene = PatternGene(
            visual=self.visual,
            audio=self.audio,
            semantic=self.semantic
        )
        
        if random.random() < mutation_rate:
            new_gene.visual = random.choice(list(VisualPatternCode))
        if random.random() < mutation_rate:
            new_gene.audio = random.choice(list(AudioPatternCode))
        if random.random() < mutation_rate:
            new_gene.semantic = random.choice(list(SemanticIntent))
        
        return new_gene
    
    def to_dict(self) -> Dict:
        return {
            "visual": self.visual.value,
            "audio": self.audio.value,
            "semantic": self.semantic.value
        }


@dataclass
class PatternChromosome:
    """패턴 시퀀스 염색체 (여러 PatternGene의 조합)"""
    genes: List[PatternGene] = field(default_factory=list)
    fitness: float = 0.0
    
    @classmethod
    def random(cls, length: int = 5) -> "PatternChromosome":
        """랜덤 염색체 생성"""
        genes = [
            PatternGene(
                visual=random.choice(list(VisualPatternCode)),
                audio=random.choice(list(AudioPatternCode)),
                semantic=random.choice(list(SemanticIntent))
            )
            for _ in range(length)
        ]
        return cls(genes=genes)
    
    def crossover(self, other: "PatternChromosome") -> Tuple["PatternChromosome", "PatternChromosome"]:
        """교차 (Two-point crossover)"""
        if len(self.genes) != len(other.genes):
            raise ValueError("Chromosomes must have same length")
        
        length = len(self.genes)
        point1 = random.randint(0, length - 2)
        point2 = random.randint(point1 + 1, length)
        
        child1_genes = self.genes[:point1] + other.genes[point1:point2] + self.genes[point2:]
        child2_genes = other.genes[:point1] + self.genes[point1:point2] + other.genes[point2:]
        
        return (
            PatternChromosome(genes=child1_genes),
            PatternChromosome(genes=child2_genes)
        )
    
    def mutate(self, mutation_rate: float = 0.1) -> "PatternChromosome":
        """돌연변이 적용"""
        mutated_genes = [gene.mutate(mutation_rate) for gene in self.genes]
        return PatternChromosome(genes=mutated_genes)
    
    def to_dict(self) -> Dict:
        return {
            "sequence": [gene.to_dict() for gene in self.genes],
            "fitness": self.fitness,
            "length": len(self.genes)
        }


class ViralPatternGA:
    """
    유전 알고리즘 기반 바이럴 패턴 최적화 엔진
    
    목표: 주어진 카테고리/문맥에서 최적의 패턴 시퀀스 발견
    
    Fitness Function:
    - PatternConfidence 테이블의 confidence_score 활용
    - 높은 신뢰도 패턴 조합 = 높은 fitness
    """
    
    def __init__(
        self,
        population_size: int = 50,
        sequence_length: int = 5,
        mutation_rate: float = 0.1,
        elite_ratio: float = 0.1
    ):
        self.population_size = population_size
        self.sequence_length = sequence_length
        self.mutation_rate = mutation_rate
        self.elite_count = max(1, int(population_size * elite_ratio))
        
        # 패턴 신뢰도 캐시 (DB에서 로드)
        self.pattern_confidences: Dict[str, float] = {}
    
    def initialize_population(self) -> List[PatternChromosome]:
        """초기 Population 생성"""
        return [
            PatternChromosome.random(self.sequence_length)
            for _ in range(self.population_size)
        ]
    
    def calculate_fitness(self, chromosome: PatternChromosome) -> float:
        """
        Fitness 계산
        
        기본 전략:
        1. 각 패턴의 confidence_score 합산
        2. 인접 패턴 간 전환(transition) 점수 추가
        3. 전체 시퀀스의 다양성 보너스
        """
        fitness = 0.0
        
        for i, gene in enumerate(chromosome.genes):
            # 1. 개별 패턴 신뢰도
            visual_conf = self.pattern_confidences.get(gene.visual.value, 0.5)
            audio_conf = self.pattern_confidences.get(gene.audio.value, 0.5)
            
            fitness += (visual_conf + audio_conf) / 2
            
            # 2. 위치 가중치 (인트로/클라이맥스 더 중요)
            if i == 0:  # 인트로
                fitness *= 1.3
            elif i == len(chromosome.genes) // 2:  # 클라이맥스
                fitness *= 1.2
        
        # 3. 다양성 보너스 (같은 패턴 반복 페널티)
        unique_visuals = len(set(g.visual for g in chromosome.genes))
        diversity_bonus = unique_visuals / len(chromosome.genes)
        fitness *= (0.8 + 0.2 * diversity_bonus)
        
        return fitness
    
    def evaluate_population(self, population: List[PatternChromosome]) -> List[PatternChromosome]:
        """전체 Population의 Fitness 계산"""
        for chromosome in population:
            chromosome.fitness = self.calculate_fitness(chromosome)
        
        return sorted(population, key=lambda c: c.fitness, reverse=True)
    
    def select_parents(self, population: List[PatternChromosome]) -> Tuple[PatternChromosome, PatternChromosome]:
        """토너먼트 선택"""
        tournament_size = 5
        tournament1 = random.sample(population, tournament_size)
        tournament2 = random.sample(population, tournament_size)
        
        parent1 = max(tournament1, key=lambda c: c.fitness)
        parent2 = max(tournament2, key=lambda c: c.fitness)
        
        return parent1, parent2
    
    def evolve(self, generations: int = 50) -> Dict:
        """
        진화 실행
        
        Returns:
            {
                "best_sequence": [...],
                "best_fitness": 0.95,
                "generations": 50,
                "improvement": 0.3
            }
        """
        # 초기화
        population = self.initialize_population()
        population = self.evaluate_population(population)
        
        initial_best = population[0].fitness
        history = [initial_best]
        
        for gen in range(generations):
            new_population = []
            
            # 엘리트 보존
            elites = population[:self.elite_count]
            new_population.extend(elites)
            
            # 교차 및 돌연변이로 새 세대 생성
            while len(new_population) < self.population_size:
                parent1, parent2 = self.select_parents(population)
                child1, child2 = parent1.crossover(parent2)
                
                child1 = child1.mutate(self.mutation_rate)
                child2 = child2.mutate(self.mutation_rate)
                
                new_population.extend([child1, child2])
            
            # 크기 맞추기
            new_population = new_population[:self.population_size]
            
            # 평가 및 정렬
            population = self.evaluate_population(new_population)
            history.append(population[0].fitness)
        
        best = population[0]
        
        return {
            "best_sequence": best.to_dict(),
            "best_fitness": round(best.fitness, 4),
            "generations": generations,
            "initial_fitness": round(initial_best, 4),
            "improvement": round(best.fitness - initial_best, 4),
            "history": history[-10:]  # 마지막 10세대
        }
    
    async def load_pattern_confidences(self, db) -> None:
        """DB에서 패턴 신뢰도 로드"""
        from app.models import PatternConfidence
        from sqlalchemy import select
        
        result = await db.execute(select(PatternConfidence))
        confidences = result.scalars().all()
        
        for conf in confidences:
            self.pattern_confidences[conf.pattern_code] = conf.confidence_score
    
    def suggest_pattern_sequence(
        self,
        category: Optional[str] = None,
        target_mood: Optional[str] = None
    ) -> Dict:
        """
        특정 조건에 맞는 최적 패턴 시퀀스 추천
        
        향후 확장:
        - 카테고리별 가중치
        - 무드별 필터링
        - 시간대별 최적화
        """
        result = self.evolve(generations=30)
        
        result["category"] = category
        result["mood"] = target_mood
        result["recommendation"] = "GA-optimized sequence based on pattern confidence data"
        
        return result


# Singleton instance
viral_pattern_ga = ViralPatternGA()
